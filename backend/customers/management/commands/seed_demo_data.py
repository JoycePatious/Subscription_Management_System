from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from billing.models import Discount, DunningAttempt, Invoice, InvoiceItem, Payment, Tax
from catalog.models import Plan, Product, ProductVariant
from customers.models import CustomerProfile
from sales.models import Quotation, QuotationItem
from subscriptions.models import Subscription, SubscriptionItem


class Command(BaseCommand):
    help = "Seeds initial demo data for Brightloop enterprise subscription platform"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # 1. Users
        admin_user, _ = User.objects.get_or_create(
            email="admin@brightloop.io",
            defaults={"username": "admin", "role": User.Role.ADMIN, "is_staff": True, "is_superuser": True},
        )
        admin_user.set_password("Password123!")
        admin_user.save()

        staff_user, _ = User.objects.get_or_create(
            email="staff@brightloop.io",
            defaults={"username": "staff", "role": User.Role.STAFF},
        )
        staff_user.set_password("Password123!")
        staff_user.save()

        acme_user, _ = User.objects.get_or_create(
            email="acme@enterprise.com",
            defaults={"username": "acme_admin", "role": User.Role.CUSTOMER},
        )
        acme_user.set_password("Password123!")
        acme_user.save()

        globex_user, _ = User.objects.get_or_create(
            email="globex@startup.io",
            defaults={"username": "globex_admin", "role": User.Role.CUSTOMER},
        )
        globex_user.set_password("Password123!")
        globex_user.save()

        initech_user, _ = User.objects.get_or_create(
            email="initech@cloud.net",
            defaults={"username": "initech_admin", "role": User.Role.CUSTOMER},
        )
        initech_user.set_password("Password123!")
        initech_user.save()

        # 2. Customer Profiles
        acme_profile, _ = CustomerProfile.objects.get_or_create(
            user=acme_user,
            defaults={
                "company_name": "Acme Corporation",
                "phone": "+1 555-0199",
                "billing_address": "100 Enterprise Way, Suite 400, San Francisco, CA 94107",
                "tax_identifier": "US-EIN-987654321",
            },
        )
        acme_profile.company_name = "Acme Corporation"
        acme_profile.save()

        globex_profile, _ = CustomerProfile.objects.get_or_create(
            user=globex_user,
            defaults={
                "company_name": "Globex SaaS Inc",
                "phone": "+1 555-0244",
                "billing_address": "550 Innovation Parkway, Austin, TX 78701",
                "tax_identifier": "US-EIN-123456789",
            },
        )
        globex_profile.company_name = "Globex SaaS Inc"
        globex_profile.save()

        initech_profile, _ = CustomerProfile.objects.get_or_create(
            user=initech_user,
            defaults={
                "company_name": "Initech Solutions",
                "phone": "+1 555-0377",
                "billing_address": "4124 Technology Drive, Seattle, WA 98101",
                "tax_identifier": "US-EIN-456789123",
            },
        )
        initech_profile.company_name = "Initech Solutions"
        initech_profile.save()

        # 3. Catalog Products
        p_platform, _ = Product.objects.get_or_create(
            name="Brightloop Enterprise Platform",
            defaults={
                "product_type": "Software",
                "sales_price": Decimal("499.00"),
                "cost_price": Decimal("80.00"),
                "notes": "Full subscription lifecycle engine with dunning and proration",
            },
        )
        p_analytics, _ = Product.objects.get_or_create(
            name="Revenue Analytics & Reporting Pro",
            defaults={
                "product_type": "Add-on",
                "sales_price": Decimal("199.00"),
                "cost_price": Decimal("30.00"),
                "notes": "Cohort retention, MRR/ARR forecasting, churn analytics",
            },
        )
        p_infra, _ = Product.objects.get_or_create(
            name="Dedicated High-Availability VPC",
            defaults={
                "product_type": "Infrastructure",
                "sales_price": Decimal("399.00"),
                "cost_price": Decimal("100.00"),
                "notes": "Isolated private VPC cluster with 99.99% uptime guarantee",
            },
        )

        ProductVariant.objects.get_or_create(
            product=p_platform,
            name="Multi-Region Active-Active",
            defaults={"price_delta": Decimal("150.00")},
        )

        # 4. Plans
        plan_starter, _ = Plan.objects.get_or_create(
            name="Starter Monthly",
            defaults={
                "price": Decimal("49.00"),
                "interval": Plan.Interval.MONTHLY,
                "description": "Essential recurring billing for growing startups",
                "allow_pause": True,
                "allow_renewal": True,
            },
        )
        plan_growth, _ = Plan.objects.get_or_create(
            name="Growth Monthly",
            defaults={
                "price": Decimal("149.00"),
                "interval": Plan.Interval.MONTHLY,
                "description": "Advanced billing with smart dunning and proration",
                "allow_pause": True,
                "allow_renewal": True,
            },
        )
        plan_scale, _ = Plan.objects.get_or_create(
            name="Scale Monthly",
            defaults={
                "price": Decimal("299.00"),
                "interval": Plan.Interval.MONTHLY,
                "description": "High volume processing, multi-currency, and API priority",
                "allow_pause": True,
                "allow_renewal": True,
            },
        )
        plan_enterprise, _ = Plan.objects.get_or_create(
            name="Enterprise Monthly",
            defaults={
                "price": Decimal("799.00"),
                "interval": Plan.Interval.MONTHLY,
                "description": "Custom workflows, enterprise SLA, dedicated account manager",
                "allow_pause": True,
                "allow_renewal": True,
            },
        )
        plan_annual, _ = Plan.objects.get_or_create(
            name="Enterprise Annual",
            defaults={
                "price": Decimal("7990.00"),
                "interval": Plan.Interval.YEARLY,
                "description": "Full enterprise suite with annual savings discount",
                "allow_pause": False,
                "allow_renewal": True,
            },
        )

        # 5. Taxes & Discounts
        Tax.objects.get_or_create(name="Standard GST", defaults={"rate": Decimal("18.00"), "is_active": True})
        Tax.objects.get_or_create(name="US State Sales Tax", defaults={"rate": Decimal("8.50"), "is_active": True})
        Discount.objects.get_or_create(
            name="ENTERPRISE20",
            defaults={
                "kind": Discount.Kind.PERCENT,
                "value": Decimal("20.00"),
                "applies_to_subscription": True,
                "is_active": True,
            },
        )

        # 6. Subscriptions
        today = timezone.localdate()
        cycle_start_acme = today - timedelta(days=15)
        cycle_end_acme = cycle_start_acme + timedelta(days=30)

        sub_acme, _ = Subscription.objects.get_or_create(
            number="SUB-ACME-001",
            defaults={
                "customer": acme_profile,
                "plan": plan_growth,
                "start_date": cycle_start_acme,
                "next_billing_date": cycle_end_acme,
                "status": Subscription.Status.ACTIVE,
                "payment_terms": "Net 30",
            },
        )
        SubscriptionItem.objects.get_or_create(
            subscription=sub_acme,
            product=p_platform,
            defaults={"quantity": 1, "unit_price": Decimal("149.00"), "tax_rate": Decimal("0")},
        )

        # Sub 2: Globex - IN_GRACE_PERIOD
        cycle_start_globex = today - timedelta(days=2)
        cycle_end_globex = cycle_start_globex + timedelta(days=30)
        sub_globex, _ = Subscription.objects.get_or_create(
            number="SUB-GLOBEX-002",
            defaults={
                "customer": globex_profile,
                "plan": plan_scale,
                "start_date": cycle_start_globex,
                "next_billing_date": cycle_end_globex,
                "status": Subscription.Status.IN_GRACE_PERIOD,
                "payment_terms": "Due upon receipt",
            },
        )
        sub_globex.status = Subscription.Status.IN_GRACE_PERIOD
        sub_globex.save()

        # Sub 3: Initech - SUSPENDED
        cycle_start_initech = today - timedelta(days=20)
        cycle_end_initech = cycle_start_initech + timedelta(days=30)
        sub_initech, _ = Subscription.objects.get_or_create(
            number="SUB-INITECH-003",
            defaults={
                "customer": initech_profile,
                "plan": plan_starter,
                "start_date": cycle_start_initech,
                "next_billing_date": cycle_end_initech,
                "status": Subscription.Status.SUSPENDED,
                "payment_terms": "Due upon receipt",
            },
        )
        sub_initech.status = Subscription.Status.SUSPENDED
        sub_initech.save()

        # 7. Invoices & Dunning Lifecycle
        # Invoice 1: Acme - Paid
        inv_acme, _ = Invoice.objects.get_or_create(
            number="INV-2026-001",
            defaults={
                "customer": acme_profile,
                "subscription": sub_acme,
                "billing_period_start": cycle_start_acme,
                "billing_period_end": cycle_end_acme,
                "issue_date": cycle_start_acme,
                "due_date": cycle_end_acme,
                "subtotal": Decimal("149.00"),
                "total": Decimal("149.00"),
                "status": Invoice.Status.PAID,
            },
        )
        InvoiceItem.objects.get_or_create(
            invoice=inv_acme,
            description="Growth Monthly Subscription",
            defaults={"quantity": 1, "unit_price": Decimal("149.00"), "line_total": Decimal("149.00")},
        )
        Payment.objects.get_or_create(
            invoice=inv_acme,
            defaults={
                "method": "Credit Card (Visa ···· 4242)",
                "amount": Decimal("149.00"),
                "paid_on": cycle_start_acme,
                "reference": "ch_acme_success_001",
            },
        )

        # Invoice 2: Globex - PAYMENT_FAILED (In Grace Period)
        now = timezone.now()
        first_failed_globex = now - timedelta(days=2)
        grace_end_globex = first_failed_globex + timedelta(days=7)

        inv_globex, _ = Invoice.objects.get_or_create(
            number="INV-2026-002",
            defaults={
                "customer": globex_profile,
                "subscription": sub_globex,
                "billing_period_start": cycle_start_globex,
                "billing_period_end": cycle_end_globex,
                "issue_date": cycle_start_globex,
                "due_date": cycle_start_globex,
                "subtotal": Decimal("299.00"),
                "total": Decimal("299.00"),
                "status": Invoice.Status.PAYMENT_FAILED,
                "first_failed_at": first_failed_globex,
                "grace_period_end": grace_end_globex,
                "first_failure_reason": "Card declined: Insufficient funds (gateway code 51)",
                "dunning_notification_logged_at": first_failed_globex,
            },
        )
        InvoiceItem.objects.get_or_create(
            invoice=inv_globex,
            description="Scale Monthly Subscription",
            defaults={"quantity": 1, "unit_price": Decimal("299.00"), "line_total": Decimal("299.00")},
        )

        # Dunning attempts for Globex:
        # Attempt 1: Failed on Day 1
        DunningAttempt.objects.get_or_create(
            invoice=inv_globex,
            attempt_number=1,
            defaults={
                "subscription": sub_globex,
                "attempt_date": first_failed_globex + timedelta(days=1),
                "scheduled_for": first_failed_globex + timedelta(days=1),
                "status": DunningAttempt.Status.FAILED,
                "failure_reason": "Simulated Gateway: Insufficient Funds",
                "simulated_gateway_response": {"status": "failed", "reason": "insufficient_funds", "code": "51"},
            },
        )
        # Attempt 2: Scheduled for Day 3 (Pending)
        DunningAttempt.objects.get_or_create(
            invoice=inv_globex,
            attempt_number=2,
            defaults={
                "subscription": sub_globex,
                "scheduled_for": first_failed_globex + timedelta(days=3),
                "status": DunningAttempt.Status.PENDING,
            },
        )
        # Attempt 3: Scheduled for Day 7 (Pending)
        DunningAttempt.objects.get_or_create(
            invoice=inv_globex,
            attempt_number=3,
            defaults={
                "subscription": sub_globex,
                "scheduled_for": first_failed_globex + timedelta(days=7),
                "status": DunningAttempt.Status.PENDING,
            },
        )

        # Invoice 3: Initech - PAYMENT_FAILED (Grace Period Expired, Suspended)
        first_failed_initech = now - timedelta(days=10)
        grace_end_initech = first_failed_initech + timedelta(days=7)

        inv_initech, _ = Invoice.objects.get_or_create(
            number="INV-2026-003",
            defaults={
                "customer": initech_profile,
                "subscription": sub_initech,
                "billing_period_start": cycle_start_initech,
                "billing_period_end": cycle_end_initech,
                "issue_date": cycle_start_initech,
                "due_date": cycle_start_initech,
                "subtotal": Decimal("49.00"),
                "total": Decimal("49.00"),
                "status": Invoice.Status.PAYMENT_FAILED,
                "first_failed_at": first_failed_initech,
                "grace_period_end": grace_end_initech,
                "first_failure_reason": "Account closed or invalid payment method",
                "dunning_notification_logged_at": first_failed_initech,
            },
        )
        InvoiceItem.objects.get_or_create(
            invoice=inv_initech,
            description="Starter Monthly Subscription",
            defaults={"quantity": 1, "unit_price": Decimal("49.00"), "line_total": Decimal("49.00")},
        )

        # 3 Failed attempts for Initech
        for num, day in enumerate((1, 3, 7), start=1):
            DunningAttempt.objects.get_or_create(
                invoice=inv_initech,
                attempt_number=num,
                defaults={
                    "subscription": sub_initech,
                    "attempt_date": first_failed_initech + timedelta(days=day),
                    "scheduled_for": first_failed_initech + timedelta(days=day),
                    "status": DunningAttempt.Status.FAILED,
                    "failure_reason": "Payment method expired or revoked by customer",
                    "simulated_gateway_response": {"status": "failed", "reason": "card_expired"},
                },
            )

        # 8. Quotations
        q1, _ = Quotation.objects.get_or_create(
            number="QT-2026-001",
            defaults={
                "customer": acme_profile,
                "status": Quotation.Status.SENT,
                "valid_until": today + timedelta(days=14),
                "created_by": admin_user,
            },
        )
        QuotationItem.objects.get_or_create(
            quotation=q1,
            product=p_platform,
            defaults={"quantity": 1, "unit_price": Decimal("12000.00"), "tax_rate": Decimal("0")},
        )

        q2, _ = Quotation.objects.get_or_create(
            number="QT-2026-002",
            defaults={
                "customer": globex_profile,
                "status": Quotation.Status.DRAFT,
                "valid_until": today + timedelta(days=7),
                "created_by": staff_user,
            },
        )
        QuotationItem.objects.get_or_create(
            quotation=q2,
            product=p_analytics,
            defaults={"quantity": 1, "unit_price": Decimal("5000.00"), "tax_rate": Decimal("0")},
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
        self.stdout.write("Credentials:")
        self.stdout.write("  Admin: admin@brightloop.io / Password123!")
        self.stdout.write("  Staff: staff@brightloop.io / Password123!")
        self.stdout.write("  Customer (Acme): acme@enterprise.com / Password123!")
        self.stdout.write("  Customer (Globex): globex@startup.io / Password123!")
