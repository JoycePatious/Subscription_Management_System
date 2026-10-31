from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Creates users by email. Passwords are hashed via set_password()."""

    use_in_migrations = True

    def _unique_username(self, base):
        base = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in (base or "user"))[:30] or "user"
        username = base
        suffix = 1
        while self.model.objects.filter(username=username).exists():
            username = f"{base}{suffix}"
            suffix += 1
        return username

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email).lower().strip()
        extra_fields.setdefault("username", self._unique_username(email.split("@")[0]))
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.CUSTOMER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        STAFF = "STAFF", "Staff"
        CUSTOMER = "CUSTOMER", "Customer"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.CUSTOMER)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        # Business STAFF is not Django admin. Only ADMIN may use /admin/.
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_staff_role(self):
        return self.role == self.Role.STAFF

    @property
    def is_customer_role(self):
        return self.role == self.Role.CUSTOMER
