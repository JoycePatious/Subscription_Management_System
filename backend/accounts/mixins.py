from .models import User


class CustomerOwnedQuerysetMixin:
    """
    Customers only see their own rows. Admin and staff see everything.
    Set customer_user_field to the lookup from this model to User
    (for example "customer__user" or "user").
    """

    customer_user_field = "customer__user"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.role == User.Role.CUSTOMER:
            return qs.filter(**{self.customer_user_field: user})
        return qs
