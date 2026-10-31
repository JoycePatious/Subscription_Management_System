from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail


def send_password_reset_email(user):
    token = default_token_generator.make_token(user)
    timeout_minutes = settings.PASSWORD_RESET_TIMEOUT // 60
    send_mail(
        subject="Brightloop password reset",
        message=(
            "Use this token with POST /api/auth/password-reset/confirm/ to set a new password.\n"
            f"The token expires in {timeout_minutes} minutes.\n\n"
            f"Email: {user.email}\n"
            f"Token: {token}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return token
