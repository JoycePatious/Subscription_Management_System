from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Full system access. Used for staff creation and other admin-only writes."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "ADMIN")


class IsStaff(BasePermission):
    """Business STAFF role only — not Django admin and not ADMIN."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "STAFF")


class IsAdminOrStaff(BasePermission):
    """Daily operations (customers, quotations, billing writes) for Admin and Staff."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in ("ADMIN", "STAFF"))


class IsAdminOrReadOnly(BasePermission):
    """Authenticated users may read; only Admin may create/update/delete."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (request.method in SAFE_METHODS or user.role == "ADMIN")
        )


class IsAdminOrStaffOrCustomerReadOwn(BasePermission):
    """
    Admin/Staff: full HTTP access.
    Customer: GET/HEAD/OPTIONS only. Pair this with CustomerOwnedQuerysetMixin
    so a customer never receives another customer's rows (404, not 403).
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.role in ("ADMIN", "STAFF"):
            return True
        if user.role == "CUSTOMER":
            return request.method in SAFE_METHODS
        return False
