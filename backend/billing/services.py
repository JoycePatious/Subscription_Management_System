from decimal import Decimal
from django.db import transaction, IntegrityError
from django.utils import timezone
from .models import Invoice, InvoiceItem

@transaction.atomic
def generate_invoice_for_subscription(subscription, period_start, period_end, due_date):
    '''
    Basic idempotent invoice-generation scaffold.
    UniqueConstraint on subscription + billing period prevents duplicate invoices.
    Production version must calculate discounts/taxes, lock subscription rows,
    handle retries, and run from a scheduler/worker.
    '''
    invoice, created = Invoice.objects.get_or_create(
        subscription=subscription,
        billing_period_start=period_start,
        billing_period_end=period_end,
        defaults={
            "number": f"INV-{subscription.number}-{period_start:%Y%m%d}",
            "customer": subscription.customer,
            "issue_date": timezone.localdate(),
            "due_date": due_date,
        }
    )
    if created:
        subtotal = Decimal("0.00")
        for item in subscription.items.select_related("product"):
            line = item.unit_price * item.quantity
            subtotal += line
            InvoiceItem.objects.create(
                invoice=invoice, description=item.product.name,
                quantity=item.quantity, unit_price=item.unit_price,
                tax_rate=item.tax_rate, line_total=line
            )
        invoice.subtotal = subtotal
        invoice.total = subtotal
        invoice.save(update_fields=["subtotal", "total"])
    return invoice
