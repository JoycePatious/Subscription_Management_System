import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordComplexityValidator:
    """Passwords must be > 8 chars and include upper, lower, and special characters."""

    def validate(self, password, user=None):
        if len(password) <= 8:
            raise ValidationError(
                _("Password must be longer than 8 characters."),
                code="password_too_short",
            )
        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code="password_no_upper",
            )
        if not re.search(r"[a-z]", password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code="password_no_lower",
            )
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(
                _("Password must contain at least one special character."),
                code="password_no_special",
            )

    def get_help_text(self):
        return _(
            "Your password must be longer than 8 characters and include uppercase, "
            "lowercase, and special characters."
        )
