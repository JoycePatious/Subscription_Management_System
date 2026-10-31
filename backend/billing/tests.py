from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import DunningAttempt, Invoice, Payment
from billing.services.dunning_service import (
    check_grace_period_expirations,
    execute_dunning_retry,
    process_payment_failure,
)
from billing.services import generate_invoice_for_subscription
from catalog.models import Plan
from subscriptions.models import Subscription
from subscriptions.services.proration_service import (
    apply_plan_change,
    calculate_proration,
)


class BusinessLogicTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("billing@example.com", "ValidPass1!")
        self.customer = self.user.customer_profile
        self.old_plan = Plan.objects.create(
            name="Starter",
            price=Decimal("30.00"),
            interval=Plan.Interval.MONTHLY,
        )
        self.new_plan = Plan.objects.create(
            name="Growth",
            price=Decimal("60.00"),
            interval=Plan.Interval.MONTHLY,
        )
        self.subscription = Subscription.objects.create(
            number="SUB-001",
            customer=self.customer,
            plan=self.old_plan,
            start_date=date(2026, 5, 1),
            next_billing_date=date(2026, 5, 31),
            status=Subscription.Status.ACTIVE,
        )
        self.invoice = Invoice.objects.create(
            number="INV-001",
            customer=self.customer,
            subscription=self.subscription,
            billing_period_start=date(2026, 5, 1),
            billing_period_end=date(2026, 5, 31),
            issue_date=date(2026, 5, 1),
            due_date=date(2026, 5, 31),
            status=Invoice.Status.CONFIRMED,
        )


class ProrationServiceTests(BusinessLogicTestCase):
    def test_proration_uses_exact_30_day_cycle(self):
        result = calculate_proration(
            self.subscription,
            self.new_plan,
            effective_date=date(2026, 5, 16),
        )

        self.assertEqual(result["total_days"], 30)
        self.assertEqual(result["used_days"], 15)
        self.assertEqual(result["remaining_days"], 15)
        self.assertEqual(result["credit"], Decimal("15.00"))
        self.assertEqual(result["new_charge"], Decimal("30.00"))
        self.assertEqual(result["adjustment"], Decimal("15.00"))

    def test_proration_uses_exact_31_day_cycle(self):
        self.subscription.start_date = date(2026, 1, 1)
        self.subscription.next_billing_date = date(2026, 2, 1)
        self.subscription.save(update_fields=["start_date", "next_billing_date"])
        self.old_plan.price = Decimal("31.00")
        self.old_plan.save(update_fields=["price"])
        self.new_plan.price = Decimal("62.00")
        self.new_plan.save(update_fields=["price"])

        result = calculate_proration(
            self.subscription,
            self.new_plan,
            effective_date=date(2026, 1, 16),
        )

        self.assertEqual(result["total_days"], 31)
        self.assertEqual(result["used_days"], 15)
        self.assertEqual(result["remaining_days"], 16)
        self.assertEqual(result["credit"], Decimal("16.00"))
        self.assertEqual(result["new_charge"], Decimal("32.00"))
        self.assertEqual(result["adjustment"], Decimal("16.00"))

    @patch("subscriptions.services.proration_service.timezone.localdate")
    def test_apply_plan_change_creates_signed_adjustment_lines(self, localdate):
        localdate.return_value = date(2026, 5, 16)

        updated, invoice, breakdown = apply_plan_change(self.subscription, self.new_plan)

        self.assertEqual(updated.plan, self.new_plan)
        self.assertEqual(breakdown["adjustment"], Decimal("15.00"))
        self.assertTrue(invoice.is_adjustment)
        self.assertEqual(invoice.status, Invoice.Status.DRAFT)
        self.assertEqual(
            list(invoice.items.order_by("id").values_list("line_total", flat=True)),
            [Decimal("-15.00"), Decimal("30.00")],
        )
        self.assertIn("15/30 days", invoice.items.first().description)

    @patch("subscriptions.services.proration_service.timezone.localdate")
    def test_deferred_adjustment_is_applied_to_next_regular_invoice(self, localdate):
        localdate.return_value = date(2026, 5, 16)
        _, adjustment, _ = apply_plan_change(
            self.subscription,
            self.new_plan,
            immediate_invoice=False,
        )

        self.assertTrue(adjustment.is_deferred_adjustment)
        self.assertEqual(adjustment.due_date, date(2026, 5, 31))
        invoice = generate_invoice_for_subscription(
            self.subscription,
            date(2026, 5, 31),
            date(2026, 6, 30),
            date(2026, 5, 31),
        )

        self.assertEqual(
            list(invoice.items.values_list("line_total", flat=True)),
            [Decimal("-15.00"), Decimal("30.00")],
        )
        self.assertEqual(invoice.total, Decimal("15.00"))
        adjustment.refresh_from_db()
        self.assertEqual(adjustment.status, Invoice.Status.CANCELLED)

    def test_plan_change_rejected_for_suspended_subscription(self):
        self.subscription.status = Subscription.Status.SUSPENDED
        self.subscription.save(update_fields=["status"])

        with self.assertRaises(ValidationError):
            apply_plan_change(self.subscription, self.new_plan)


class DunningServiceTests(BusinessLogicTestCase):
    @patch("billing.services.dunning_service.timezone.now")
    def test_three_failed_retries_suspend_after_grace_period(self, now):
        first_failure = timezone.make_aware(datetime(2026, 5, 1, 10, 0))
        now.return_value = first_failure
        process_payment_failure(self.invoice, "card declined")

        self.invoice.refresh_from_db()
        self.subscription.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAYMENT_FAILED)
        self.assertEqual(self.subscription.status, Subscription.Status.IN_GRACE_PERIOD)
        self.assertEqual(
            list(self.invoice.dunning_attempts.values_list("scheduled_for", flat=True)),
            [
                first_failure + timedelta(days=1),
                first_failure + timedelta(days=3),
                first_failure + timedelta(days=7),
            ],
        )

        now.return_value = first_failure + timedelta(days=8)
        for _ in range(3):
            execute_dunning_retry(self.invoice, {"status": "failed", "reason": "declined"})

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.SUSPENDED)
        self.assertEqual(
            self.invoice.dunning_attempts.filter(status=DunningAttempt.Status.FAILED).count(),
            3,
        )
        self.assertEqual(check_grace_period_expirations(), [])

    @patch("billing.services.dunning_service.timezone.now")
    def test_successful_retry_restores_subscription_and_skips_remaining(self, now):
        first_failure = timezone.make_aware(datetime(2026, 5, 1, 10, 0))
        now.return_value = first_failure
        process_payment_failure(self.invoice, "card declined")
        now.return_value = first_failure + timedelta(days=1)

        attempt = execute_dunning_retry(self.invoice, {"status": "succeeded", "reference": "mock"})

        self.invoice.refresh_from_db()
        self.subscription.refresh_from_db()
        self.assertEqual(attempt.status, DunningAttempt.Status.SUCCEEDED)
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)
        self.assertEqual(self.subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(
            self.invoice.dunning_attempts.filter(status=DunningAttempt.Status.SKIPPED).count(),
            2,
        )

    def test_staff_dunning_endpoints_and_customer_write_restriction(self):
        self.invoice.total = Decimal("25.00")
        self.invoice.save(update_fields=["total"])
        client = APIClient()
        client.force_authenticate(self.user)
        denied = client.post(
            f"/api/billing/invoices/{self.invoice.pk}/record-failure/",
            {"reason": "declined"},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

        staff = User.objects.create_user(
            "staff@example.com",
            "ValidPass1!",
            role=User.Role.STAFF,
        )
        client.force_authenticate(staff)
        failure = client.post(
            f"/api/billing/invoices/{self.invoice.pk}/record-failure/",
            {"reason": "card declined"},
            format="json",
        )
        self.assertEqual(failure.status_code, 200, failure.data)

        history = client.get(f"/api/billing/invoices/{self.invoice.pk}/dunning-history/")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.data), 3)

        Payment.objects.create(
            invoice=self.invoice,
            method="card",
            amount=Decimal("25.00"),
            paid_on=date(2026, 5, 2),
        )
        retry = client.post(f"/api/billing/invoices/{self.invoice.pk}/retry-payment/")
        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertEqual(retry.data["status"], DunningAttempt.Status.SUCCEEDED)

    def test_customer_can_only_preview_owned_subscriptions(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post(
            f"/api/subscriptions/{self.subscription.pk}/preview-proration/",
            {"new_plan_id": self.new_plan.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        with patch("subscriptions.services.proration_service.timezone.localdate") as localdate:
            localdate.return_value = date(2026, 5, 16)
            changed = client.post(
                f"/api/subscriptions/{self.subscription.pk}/change-plan/",
                {"new_plan_id": self.new_plan.pk, "immediate_invoice": False},
                format="json",
            )
        self.assertEqual(changed.status_code, 200, changed.data)
        self.assertEqual(changed.data["subscription"]["plan"], self.new_plan.pk)
        self.assertTrue(changed.data["invoice"]["is_deferred_adjustment"])

        other_user = User.objects.create_user("other@example.com", "ValidPass1!")
        other_customer = other_user.customer_profile
        other_subscription = Subscription.objects.create(
            number="SUB-002",
            customer=other_customer,
            plan=self.old_plan,
            start_date=date(2026, 5, 1),
            next_billing_date=date(2026, 5, 31),
            status=Subscription.Status.ACTIVE,
        )
        forbidden = client.post(
            f"/api/subscriptions/{other_subscription.pk}/preview-proration/",
            {"new_plan_id": self.new_plan.pk},
            format="json",
        )
        self.assertEqual(forbidden.status_code, 404)
