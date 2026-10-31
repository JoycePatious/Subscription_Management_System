# Initial data model

- User: authentication identity and role.
- CustomerProfile: business/customer profile linked to a user.
- Product → ProductVariant: product catalog and optional variant price delta.
- Plan: billing interval, base price, quantity and availability rules.
- QuotationTemplate → Quotation → QuotationItem: reusable offers and customer quotes.
- Subscription → SubscriptionItem: customer agreement and its product/plan lines.
- Tax, Discount: reusable billing rules.
- Invoice → InvoiceItem: immutable billing snapshot for a billing period.
- Payment: payment record associated with an invoice.

## Important design decisions to make
1. Decide whether a customer can have multiple user logins.
2. Define tax-inclusive versus tax-exclusive pricing.
3. Define whether partial payments are allowed.
4. Define how refunds, failed payments, proration, and plan changes work.
5. Define timezone and exact renewal-day behavior (e.g. Jan 31 monthly renewal).
6. Store invoice line descriptions, prices, tax rates, and discounts as snapshots so later catalog edits do not rewrite historical invoices.
7. Use a database transaction and a unique billing-period key to prevent duplicate invoices when two workers run at once.
