"""
Smart Dunning & Automated Grace-Period Engine for Brightloop Billing.

Business Logic & State Machine Architecture:
---------------------------------------------
1. Subscription Statuses:
   - ACTIVE: Normal operating state with active entitlement.
   - PAST_DUE: Payment overdue but within initial grace window.
   - IN_GRACE_PERIOD: Entered upon first payment failure. Entitlement degraded/monitored.
   - SUSPENDED: Entitlement revoked after 7-day grace period expires with all 3 retries failed.
   - CANCELED: Subscription closed; exempted from dunning.

2. Invoice Payment Statuses:
   - DRAFT: Initial invoice creation.
   - CONFIRMED: Finalized invoice awaiting payment.
   - PAYMENT_FAILED: Payment declined; enters dunning lifecycle.
   - PAID: Successfully settled invoice.

3. Grace Period & Retry Schedule:
   - Grace Window: Exactly 7 days from the initial failure timestamp (first_failed_at).
   - Retry Spacing: Exactly 3 automatic retry attempts spaced across the grace period:
     * Attempt 1: +1 day after initial failure
     * Attempt 2: +3 days after initial failure
     * Attempt 3: +7 days after initial failure (grace period boundary)

4. Entitlement Degradation & Restoration Flow:
   - First failure:
     * Invoice status -> PAYMENT_FAILED
     * Subscription status -> IN_GRACE_PERIOD
     * Schedules 3 DunningAttempt rows (attempt_number: 1, 2, 3)
   - Successful retry on any attempt:
     * Invoice status -> PAID
     * Subscription status -> ACTIVE (immediate restoration)
     * Remaining pending attempts -> SKIPPED
   - Exhaustion after 7 days:
     * If all 3 attempts have status FAILED and now >= grace_period_end:
     * Subscription status -> SUSPENDED (entitlement terminated)
"""

from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from billing.models import DunningAttempt, Invoice
from subscriptions.models import Subscription


RETRY_DAYS = (1, 3, 7)
GRACE_PERIOD_DAYS = 7


def _simulate_gateway_payment(invoice):
    """
    Simulate gateway payment outcome based on recorded payments.
    
    If payments recorded against the invoice meet or exceed the total,
    simulates a successful gateway transaction. Otherwise returns a simulated decline.
    """
    recorded_amount = invoice.payments.aggregate(total=Sum("amount"))["total"]
    if recorded_amount is not None and recorded_amount >= invoice.total:
        return {
            "status": "succeeded",
            "source": "recorded_payment",
            "amount": str(recorded_amount),
        }
    return {"status": "failed", "reason": "simulated_payment_declined"}


@transaction.atomic
def process_payment_failure(invoice, reason):
    """
    Process an initial or repeated payment failure on an invoice.

    Transitions:
    - Invoice: -> PAYMENT_FAILED
    - Subscription: ACTIVE -> IN_GRACE_PERIOD
    - Creates 3 scheduled DunningAttempt records for Day 1, Day 3, and Day 7.

    Guarantees:
    - Atomically locks invoice and subscription records via select_for_update().
    - Idempotent: Repeated failure notifications preserve the original first_failed_at timestamp.
    """
    locked_invoice = Invoice.objects.select_for_update().select_related("subscription").get(pk=invoice.pk)
    if locked_invoice.status == Invoice.Status.PAID:
        raise ValueError("A paid invoice cannot enter dunning.")
    if locked_invoice.status == Invoice.Status.CANCELLED:
        raise ValueError("A canceled invoice cannot enter dunning.")

    now = timezone.now()
    if locked_invoice.first_failed_at is None:
        locked_invoice.first_failed_at = now
        locked_invoice.grace_period_end = now + timedelta(days=GRACE_PERIOD_DAYS)
        locked_invoice.first_failure_reason = reason
        locked_invoice.dunning_notification_logged_at = now

    locked_invoice.status = Invoice.Status.PAYMENT_FAILED
    locked_invoice.save(
        update_fields=[
            "status",
            "first_failed_at",
            "grace_period_end",
            "first_failure_reason",
            "dunning_notification_logged_at",
        ]
    )

    subscription = Subscription.objects.select_for_update().get(pk=locked_invoice.subscription_id)
    if subscription.status not in (Subscription.Status.SUSPENDED, Subscription.Status.CANCELED):
        subscription.status = Subscription.Status.IN_GRACE_PERIOD
        subscription.save(update_fields=["status"])

    for attempt_number, day in enumerate(RETRY_DAYS, start=1):
        DunningAttempt.objects.get_or_create(
            invoice=locked_invoice,
            attempt_number=attempt_number,
            defaults={
                "subscription": subscription,
                "scheduled_for": locked_invoice.first_failed_at + timedelta(days=day),
            },
        )
    return locked_invoice


@transaction.atomic
def execute_dunning_retry(invoice, gateway_response=None, force=False):
    """
    Execute the earliest pending retry, recording its gateway outcome atomically.
    Supplying a response is useful for gateway adapters and deterministic tests.
    """
    locked_invoice = Invoice.objects.select_for_update().select_related("subscription").get(pk=invoice.pk)
    if locked_invoice.status == Invoice.Status.PAID:
        return None
    if locked_invoice.status != Invoice.Status.PAYMENT_FAILED:
        raise ValueError("The invoice has no failed payment to retry.")

    attempt = (
        DunningAttempt.objects.select_for_update()
        .filter(invoice=locked_invoice, status=DunningAttempt.Status.PENDING)
        .order_by("attempt_number")
        .first()
    )
    if attempt is None:
        raise ValueError("No dunning retries remain for this invoice.")
    if not force and attempt.scheduled_for > timezone.now():
        raise ValueError("The next payment retry is not scheduled yet.")

    response = gateway_response if gateway_response is not None else _simulate_gateway_payment(locked_invoice)
    succeeded = response.get("status") in ("succeeded", "success", "paid")
    attempt.attempt_date = timezone.now()
    attempt.simulated_gateway_response = response
    if succeeded:
        attempt.status = DunningAttempt.Status.SUCCEEDED
        attempt.failure_reason = ""
        locked_invoice.status = Invoice.Status.PAID
        locked_invoice.save(update_fields=["status"])
        subscription = Subscription.objects.select_for_update().get(pk=locked_invoice.subscription_id)
        subscription.status = Subscription.Status.ACTIVE
        subscription.save(update_fields=["status"])
        locked_invoice.dunning_attempts.filter(status=DunningAttempt.Status.PENDING).update(
            status=DunningAttempt.Status.SKIPPED,
            failure_reason="Invoice was paid by an earlier retry.",
        )
    else:
        attempt.status = DunningAttempt.Status.FAILED
        attempt.failure_reason = str(response.get("reason", "Payment retry failed."))
    attempt.save(
        update_fields=[
            "attempt_date",
            "status",
            "failure_reason",
            "simulated_gateway_response",
        ]
    )

    if not succeeded and locked_invoice.grace_period_end and timezone.now() >= locked_invoice.grace_period_end:
        _suspend_if_all_retries_failed(locked_invoice)
    return attempt


def _suspend_if_all_retries_failed(invoice):
    attempts = list(invoice.dunning_attempts.all())
    if len(attempts) != len(RETRY_DAYS) or any(
        attempt.status != DunningAttempt.Status.FAILED for attempt in attempts
    ):
        return False
    subscription = Subscription.objects.select_for_update().get(pk=invoice.subscription_id)
    if subscription.status in (Subscription.Status.CANCELED, Subscription.Status.SUSPENDED):
        return False
    subscription.status = Subscription.Status.SUSPENDED
    subscription.save(update_fields=["status"])
    return True


@transaction.atomic
def check_grace_period_expirations():
    """
    Suspend subscriptions only after the grace deadline and all three retries failed.
    """
    expired = Invoice.objects.filter(
        status=Invoice.Status.PAYMENT_FAILED,
        grace_period_end__lte=timezone.now(),
    ).select_related("subscription")
    suspended = []
    for invoice in expired:
        locked_invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        if _suspend_if_all_retries_failed(locked_invoice):
            suspended.append(locked_invoice.subscription_id)
    return suspended
