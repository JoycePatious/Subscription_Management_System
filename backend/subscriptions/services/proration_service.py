import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from billing.models import Invoice, InvoiceItem
from catalog.models import Plan
from subscriptions.models import Subscription


CENT = Decimal("0.01")


def _date_at_cycle(start_date, interval, cycle_number):
    if interval == Plan.Interval.DAILY:
        return start_date + timedelta(days=cycle_number)
    if interval == Plan.Interval.WEEKLY:
        return start_date + timedelta(weeks=cycle_number)
    if interval == Plan.Interval.MONTHLY:
        month_index = start_date.year * 12 + start_date.month - 1 + cycle_number
        year, month = divmod(month_index, 12)
        month += 1
        day = min(start_date.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    if interval == Plan.Interval.YEARLY:
        year = start_date.year + cycle_number
        day = min(start_date.day, calendar.monthrange(year, start_date.month)[1])
        return date(year, start_date.month, day)
    raise ValidationError("Unsupported plan billing interval.")


def _cycle_index_for_date(start_date, interval, target_date):
    if interval == Plan.Interval.DAILY:
        return (target_date - start_date).days
    if interval == Plan.Interval.WEEKLY:
        return (target_date - start_date).days // 7
    if interval == Plan.Interval.MONTHLY:
        index = (target_date.year - start_date.year) * 12 + target_date.month - start_date.month
    elif interval == Plan.Interval.YEARLY:
        index = target_date.year - start_date.year
    else:
        raise ValidationError("Unsupported plan billing interval.")
    while _date_at_cycle(start_date, interval, index) > target_date:
        index -= 1
    while _date_at_cycle(start_date, interval, index + 1) <= target_date:
        index += 1
    return index


def _billing_cycle(subscription, effective_date):
    interval = subscription.plan.interval
    next_billing_date = subscription.next_billing_date
    if next_billing_date and effective_date < next_billing_date:
        cycle_index = _cycle_index_for_date(subscription.start_date, interval, next_billing_date)
        indexed_end = _date_at_cycle(subscription.start_date, interval, cycle_index)
        if indexed_end == next_billing_date:
            cycle_start = _date_at_cycle(subscription.start_date, interval, cycle_index - 1)
        else:
            cycle_start = indexed_end
        cycle_end = next_billing_date
        return cycle_start, cycle_end

    cycle_index = _cycle_index_for_date(subscription.start_date, interval, effective_date)
    cycle_start = _date_at_cycle(subscription.start_date, interval, cycle_index)
    cycle_end = _date_at_cycle(subscription.start_date, interval, cycle_index + 1)
    return cycle_start, cycle_end


def calculate_proration(subscription, new_plan, effective_date=None):
    """
    Calculate the unused old-plan credit and remaining-cycle new-plan charge.
    Both amounts are rounded to the nearest cent using ROUND_HALF_UP.
    """
    effective_date = effective_date or timezone.localdate()
    if isinstance(effective_date, datetime):
        effective_date = effective_date.date()
    if not isinstance(effective_date, date):
        raise ValidationError("effective_date must be a date.")
    if not new_plan.is_active:
        raise ValidationError("The target plan is not active.")

    cycle_start, cycle_end = _billing_cycle(subscription, effective_date)
    total_days = (cycle_end - cycle_start).days
    used_days = (effective_date - cycle_start).days
    if total_days <= 0 or used_days < 0 or used_days >= total_days:
        raise ValidationError("The effective date is outside the current billing cycle.")
    remaining_days = total_days - used_days
    remaining_fraction = Decimal(remaining_days) / Decimal(total_days)
    credit = (subscription.plan.price * remaining_fraction).quantize(CENT, rounding=ROUND_HALF_UP)
    new_charge = (new_plan.price * remaining_fraction).quantize(CENT, rounding=ROUND_HALF_UP)
    adjustment = new_charge - credit
    return {
        "old_plan": subscription.plan.name,
        "new_plan": new_plan.name,
        "cycle_start": cycle_start,
        "cycle_end": cycle_end,
        "effective_date": effective_date,
        "total_days": total_days,
        "used_days": used_days,
        "remaining_days": remaining_days,
        "credit": credit,
        "new_charge": new_charge,
        "adjustment": adjustment,
    }


@transaction.atomic
def apply_plan_change(subscription, new_plan, immediate_invoice=True):
    """
    Lock and update the subscription, then create signed adjustment invoice lines.
    """
    locked_subscription = (
        Subscription.objects.select_for_update()
        .select_related("plan", "customer")
        .get(pk=subscription.pk)
    )
    if locked_subscription.status in (
        Subscription.Status.SUSPENDED,
        Subscription.Status.CANCELED,
    ):
        raise ValidationError("Suspended or canceled subscriptions cannot change plans.")
    if not new_plan.is_active:
        raise ValidationError("The target plan is not active.")

    effective_date = timezone.localdate()
    breakdown = calculate_proration(locked_subscription, new_plan, effective_date)
    old_plan = locked_subscription.plan
    locked_subscription.plan = new_plan
    locked_subscription.save(update_fields=["plan"])

    due_date = (
        effective_date
        if immediate_invoice
        else (locked_subscription.next_billing_date or breakdown["cycle_end"])
    )
    invoice = Invoice.objects.create(
        number=f"ADJ-{locked_subscription.pk}-{effective_date:%Y%m%d}-{uuid4().hex[:8].upper()}",
        customer=locked_subscription.customer,
        subscription=locked_subscription,
        billing_period_start=breakdown["cycle_start"],
        billing_period_end=breakdown["cycle_end"],
        issue_date=effective_date,
        due_date=due_date,
        subtotal=breakdown["adjustment"],
        total=breakdown["adjustment"],
        status=Invoice.Status.DRAFT,
        is_adjustment=True,
        is_deferred_adjustment=not immediate_invoice,
    )
    credit_description = (
        f"Credit: Unused {old_plan.name} "
        f"({breakdown['remaining_days']}/{breakdown['total_days']} days)"
    )
    charge_description = (
        f"Charge: Prorated {new_plan.name} "
        f"({breakdown['remaining_days']}/{breakdown['total_days']} days)"
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        description=credit_description,
        unit_price=-breakdown["credit"],
        line_total=-breakdown["credit"],
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        description=charge_description,
        unit_price=breakdown["new_charge"],
        line_total=breakdown["new_charge"],
    )
    return locked_subscription, invoice, breakdown
