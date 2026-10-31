# Problem statement coverage map

| Requirement from brief | Starter location |
|---|---|
| Unique email, password rules, reset link | `accounts/` (validation, JWT, password reset with timed tokens) |
| Admin, staff, customer roles | `accounts/models.py`, `accounts/permissions.py` |
| Admin-only staff creation | `POST /api/auth/staff/` (`IsAdmin` + `StaffCreateSerializer`) |
| Products, type, sales/cost price, notes | `catalog/models.py` |
| Product variants and price additions | `catalog/models.py` (`ProductVariant.price_delta`) |
| Daily/weekly/monthly/yearly plans, quantity, availability | `catalog/models.py` (`Plan`) |
| Pause, renew, early close, auto-close | `subscriptions/` status/actions scaffold |
| Quotation templates and validity | `sales/models.py` |
| Subscription number, dates, payment terms, lines and statuses | `subscriptions/models.py` |
| Automatic invoices, taxes, no duplicate/omitted billing | `billing/services.py` idempotency scaffold; scheduler TODO |
| Fixed/percentage discounts and eligibility limits | `billing/models.py` |
| Payments linked to invoices | `billing/models.py` |
| Active subscriptions, revenue, outstanding and overdue reports | `reports/views.py` |
| Customer self-service portal | Frontend customer portal page shell; API ownership filtering TODO |
| Under-two-second page response at scale | Pagination and indexes started; load testing and query optimization TODO |

The brief does not specify a payment gateway, email provider, tax jurisdiction, or exact accounting rules. Those should be confirmed before implementing integrations/calculations.
