from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from billing.models import Invoice, InvoiceItem


@transaction.atomic
def generate_invoice_for_subscription(subscription, period_start, period_end, due_date):
    """
    Create an idempotent regular invoice for a subscription billing period.
    """
    invoice, created = Invoice.objects.get_or_create(
        subscription=subscription,
        billing_period_start=period_start,
        billing_period_end=period_end,
        is_adjustment=False,
        defaults={
            "number": f"INV-{subscription.number}-{period_start:%Y%m%d}",
            "customer": subscription.customer,
            "issue_date": timezone.localdate(),
            "due_date": due_date,
        },
    )

    subtotal = invoice.subtotal
    adjustments_applied = False
    if created:
        subtotal = Decimal("0.00")
        for item in subscription.items.select_related("product"):
            line = item.unit_price * item.quantity
            subtotal += line
            InvoiceItem.objects.create(
                invoice=invoice,
                description=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                tax_rate=item.tax_rate,
                line_total=line,
            )

    if invoice.status not in (Invoice.Status.PAID, Invoice.Status.CANCELLED):
        deferred_adjustments = Invoice.objects.select_for_update().filter(
            subscription=subscription,
            is_adjustment=True,
            is_deferred_adjustment=True,
            status=Invoice.Status.DRAFT,
            due_date__lte=period_start,
        ).prefetch_related("items")
        for adjustment in deferred_adjustments:
            for item in adjustment.items.all():
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    tax_rate=item.tax_rate,
                    line_total=item.line_total,
                )
                subtotal += item.line_total
                adjustments_applied = True
            adjustment.status = Invoice.Status.CANCELLED
            adjustment.save(update_fields=["status"])

    if created or adjustments_applied:
        invoice.subtotal = subtotal
        invoice.total = subtotal
        invoice.save(update_fields=["subtotal", "total"])
    return invoice
