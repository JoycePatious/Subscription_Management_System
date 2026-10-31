from datetime import date, timedelta
from decimal import Decimal
import re

from django.contrib.auth.hashers import check_password
from django.core import mail
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from accounts.serializers import RegisterSerializer
from catalog.models import Plan
from customers.models import CustomerProfile
from subscriptions.models import Subscription
from billing.models import Invoice


STRONG_PASSWORD = "ValidPass1!"


def auth_headers(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class AuthFoundationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def register(self, email, password=STRONG_PASSWORD, username=None):
        payload = {"email": email, "password": password}
        if username:
            payload["username"] = username
        return self.client.post("/api/auth/register/", payload, format="json")

    def login(self, email, password=STRONG_PASSWORD):
        return self.client.post(
            "/api/auth/login/",
            {"email": email, "password": password},
            format="json",
        )

    def test_register_hashes_password_and_creates_customer(self):
        response = self.register("alex@example.com")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn("password", response.data)
        user = User.objects.get(email="alex@example.com")
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(check_password(STRONG_PASSWORD, user.password))
        self.assertNotEqual(user.password, STRONG_PASSWORD)
        self.assertTrue(CustomerProfile.objects.filter(user=user).exists())

    def test_weak_password_rejected(self):
        response = self.register("weak@example.com", password="short")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="weak@example.com").exists())

    def test_password_missing_complexity_rejected(self):
        cases = {
            "exactly8@example.com": "Abcd12!x",  # 8 chars, must be longer
            "noupper@example.com": "validpass1!",
            "nolower@example.com": "VALIDPASS1!",
            "nospecial@example.com": "ValidPass1",
        }
        for email, password in cases.items():
            with self.subTest(email=email):
                response = self.register(email, password=password)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(User.objects.filter(email=email).exists())

    def test_duplicate_email_rejected(self):
        self.assertEqual(self.register("dup@example.com").status_code, 201)
        response = self.register("DUP@example.com")
        self.assertEqual(response.status_code, 400)

    def test_register_ignores_role_spoofing(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "spoof@example.com", "password": STRONG_PASSWORD, "role": "ADMIN"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(email="spoof@example.com")
        self.assertEqual(user.role, User.Role.CUSTOMER)

    def test_login_returns_jwt(self):
        self.register("login@example.com")
        response = self.login("login@example.com")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], "CUSTOMER")

    def test_login_rejects_invalid_credentials(self):
        self.register("badlogin@example.com")
        wrong = self.login("badlogin@example.com", password="WrongPass1!")
        self.assertEqual(wrong.status_code, 401)
        missing = self.login("nobody@example.com")
        self.assertEqual(missing.status_code, 401)

    def test_me_requires_jwt(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
        self.register("me@example.com")
        token = self.login("me@example.com").data["access"]
        response = self.client.get("/api/auth/me/", **auth_headers(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "me@example.com")

    def test_token_refresh(self):
        self.register("refresh@example.com")
        tokens = self.login("refresh@example.com").data
        response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": tokens["refresh"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_refresh_rejects_invalid_token(self):
        response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": "not-a-jwt"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


class RegisterSerializerTests(TestCase):
    def test_valid_payload_creates_hashed_customer(self):
        serializer = RegisterSerializer(
            data={"email": "serial@example.com", "password": STRONG_PASSWORD}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertTrue(check_password(STRONG_PASSWORD, user.password))
        self.assertEqual(serializer.data["email"], "serial@example.com")
        self.assertNotIn("password", serializer.data)

    def test_invalid_email_and_password_surface_field_errors(self):
        User.objects.create_user("taken@example.com", STRONG_PASSWORD)
        serializer = RegisterSerializer(
            data={"email": "taken@example.com", "password": "short"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertIn("password", serializer.errors)


class RolePermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser("admin@example.com", STRONG_PASSWORD)
        self.staff = User.objects.create_user(
            "staff@example.com", STRONG_PASSWORD, role=User.Role.STAFF
        )
        self.customer = User.objects.create_user("cust@example.com", STRONG_PASSWORD)
        self.other = User.objects.create_user("other@example.com", STRONG_PASSWORD)

    def login(self, email):
        return self.client.post(
            "/api/auth/login/",
            {"email": email, "password": STRONG_PASSWORD},
            format="json",
        ).data["access"]

    def test_admin_flags_and_staff_has_no_admin_privileges(self):
        self.admin.refresh_from_db()
        self.staff.refresh_from_db()
        self.assertEqual(self.admin.role, User.Role.ADMIN)
        self.assertTrue(self.admin.is_staff)
        self.assertTrue(self.admin.is_superuser)
        self.assertEqual(self.staff.role, User.Role.STAFF)
        self.assertFalse(self.staff.is_staff)
        self.assertFalse(self.staff.is_superuser)

    def test_only_admin_can_create_staff(self):
        customer_token = self.login("cust@example.com")
        denied = self.client.post(
            "/api/auth/staff/",
            {"email": "newstaff@example.com", "password": STRONG_PASSWORD},
            format="json",
            **auth_headers(customer_token),
        )
        self.assertEqual(denied.status_code, 403)

        staff_token = self.login("staff@example.com")
        denied_staff = self.client.post(
            "/api/auth/staff/",
            {"email": "newstaff@example.com", "password": STRONG_PASSWORD},
            format="json",
            **auth_headers(staff_token),
        )
        self.assertEqual(denied_staff.status_code, 403)

        admin_token = self.login("admin@example.com")
        created = self.client.post(
            "/api/auth/staff/",
            {"email": "newstaff@example.com", "password": STRONG_PASSWORD},
            format="json",
            **auth_headers(admin_token),
        )
        self.assertEqual(created.status_code, 201, created.data)
        new_staff = User.objects.get(email="newstaff@example.com")
        self.assertEqual(new_staff.role, User.Role.STAFF)
        self.assertFalse(new_staff.is_superuser)

    def test_staff_create_ignores_admin_role_spoofing(self):
        admin_token = self.login("admin@example.com")
        created = self.client.post(
            "/api/auth/staff/",
            {
                "email": "spoofstaff@example.com",
                "password": STRONG_PASSWORD,
                "role": "ADMIN",
            },
            format="json",
            **auth_headers(admin_token),
        )
        self.assertEqual(created.status_code, 201, created.data)
        user = User.objects.get(email="spoofstaff@example.com")
        self.assertEqual(user.role, User.Role.STAFF)
        self.assertFalse(user.is_superuser)

    def test_three_roles_dashboard_and_customer_scope(self):
        admin_token = self.login("admin@example.com")
        staff_token = self.login("staff@example.com")
        customer_token = self.login("cust@example.com")

        self.assertEqual(
            self.client.get("/api/dashboard/summary/", **auth_headers(admin_token)).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/dashboard/summary/", **auth_headers(staff_token)).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/dashboard/summary/", **auth_headers(customer_token)).status_code,
            403,
        )

        staff_list = self.client.get("/api/customers/", **auth_headers(staff_token))
        self.assertEqual(staff_list.status_code, 200)
        self.assertGreaterEqual(staff_list.data["count"], 2)

    def test_customer_cannot_see_another_customer_profile(self):
        token = self.login("cust@example.com")
        other_profile = CustomerProfile.objects.get(user=self.other)
        own_profile = CustomerProfile.objects.get(user=self.customer)

        own = self.client.get(f"/api/customers/{own_profile.id}/", **auth_headers(token))
        self.assertEqual(own.status_code, 200)

        other = self.client.get(f"/api/customers/{other_profile.id}/", **auth_headers(token))
        self.assertEqual(other.status_code, 404)

        listing = self.client.get("/api/customers/", **auth_headers(token))
        self.assertEqual(listing.status_code, 200)
        ids = [row["id"] for row in listing.data["results"]]
        self.assertEqual(ids, [own_profile.id])

    def test_customer_cannot_see_another_customer_subscription(self):
        plan = Plan.objects.create(name="Monthly", price=Decimal("10.00"), interval="MONTHLY")
        own_sub = Subscription.objects.create(
            number="SUB-OWN",
            customer=self.customer.customer_profile,
            plan=plan,
            start_date=date.today(),
        )
        other_sub = Subscription.objects.create(
            number="SUB-OTHER",
            customer=self.other.customer_profile,
            plan=plan,
            start_date=date.today(),
        )
        token = self.login("cust@example.com")
        listing = self.client.get("/api/subscriptions/", **auth_headers(token))
        self.assertEqual(listing.status_code, 200)
        numbers = [row["number"] for row in listing.data["results"]]
        self.assertEqual(numbers, ["SUB-OWN"])
        self.assertEqual(
            self.client.get(f"/api/subscriptions/{other_sub.id}/", **auth_headers(token)).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(f"/api/subscriptions/{own_sub.id}/", **auth_headers(token)).status_code,
            200,
        )

    def test_customer_cannot_see_another_invoice(self):
        plan = Plan.objects.create(name="Monthly", price=Decimal("10.00"), interval="MONTHLY")
        today = date.today()
        own_sub = Subscription.objects.create(
            number="INV-OWN-SUB",
            customer=self.customer.customer_profile,
            plan=plan,
            start_date=today,
        )
        other_sub = Subscription.objects.create(
            number="INV-OTHER-SUB",
            customer=self.other.customer_profile,
            plan=plan,
            start_date=today,
        )
        Invoice.objects.create(
            number="INV-OWN",
            customer=self.customer.customer_profile,
            subscription=own_sub,
            billing_period_start=today,
            billing_period_end=today + timedelta(days=30),
            issue_date=today,
            due_date=today + timedelta(days=7),
        )
        other_invoice = Invoice.objects.create(
            number="INV-OTHER",
            customer=self.other.customer_profile,
            subscription=other_sub,
            billing_period_start=today,
            billing_period_end=today + timedelta(days=30),
            issue_date=today,
            due_date=today + timedelta(days=7),
        )
        token = self.login("cust@example.com")
        listing = self.client.get("/api/invoices/", **auth_headers(token))
        self.assertEqual(listing.status_code, 200)
        numbers = [row["number"] for row in listing.data["results"]]
        self.assertEqual(numbers, ["INV-OWN"])
        self.assertEqual(
            self.client.get(f"/api/invoices/{other_invoice.id}/", **auth_headers(token)).status_code,
            404,
        )


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("reset@example.com", STRONG_PASSWORD)

    def request_reset(self, email="reset@example.com"):
        return self.client.post("/api/auth/password-reset/", {"email": email}, format="json")

    def token_from_mailbox(self):
        self.assertEqual(len(mail.outbox), 1)
        match = re.search(r"Token: (\S+)", mail.outbox[0].body)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_reset_request_sends_email_only_when_user_exists(self):
        unknown = self.request_reset("missing@example.com")
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

        known = self.request_reset()
        self.assertEqual(known.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset@example.com", mail.outbox[0].body)

    def test_confirm_sets_new_password_and_invalidates_old(self):
        self.request_reset()
        token = self.token_from_mailbox()
        new_password = "NewValid9!"
        confirm = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"email": "reset@example.com", "token": token, "password": new_password},
            format="json",
        )
        self.assertEqual(confirm.status_code, 200, confirm.data)

        old_login = self.client.post(
            "/api/auth/login/",
            {"email": "reset@example.com", "password": STRONG_PASSWORD},
            format="json",
        )
        self.assertEqual(old_login.status_code, 401)

        new_login = self.client.post(
            "/api/auth/login/",
            {"email": "reset@example.com", "password": new_password},
            format="json",
        )
        self.assertEqual(new_login.status_code, 200)
        self.assertIn("access", new_login.data)

        reused = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"email": "reset@example.com", "token": token, "password": "Another9!"},
            format="json",
        )
        self.assertEqual(reused.status_code, 400)

    def test_confirm_rejects_invalid_token_and_weak_password(self):
        bad_token = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"email": "reset@example.com", "token": "not-a-real-token", "password": "NewValid9!"},
            format="json",
        )
        self.assertEqual(bad_token.status_code, 400)

        self.request_reset()
        token = self.token_from_mailbox()
        weak = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"email": "reset@example.com", "token": token, "password": "short"},
            format="json",
        )
        self.assertEqual(weak.status_code, 400)
        self.assertTrue(check_password(STRONG_PASSWORD, User.objects.get(email="reset@example.com").password))

