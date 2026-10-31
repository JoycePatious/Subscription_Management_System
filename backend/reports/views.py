from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAdminOrStaff
from subscriptions.models import Subscription
from billing.models import Invoice, Payment

class DashboardSummaryView(APIView):
    permission_classes=[IsAdminOrStaff]
    def get(self, request):
        today=timezone.localdate()
        active=Subscription.objects.filter(status="ACTIVE").count()
        received=Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
        invoiced=Invoice.objects.exclude(status="CANCELLED").aggregate(total=Sum("total"))["total"] or 0
        paid_invoice_ids=Payment.objects.values_list("invoice_id",flat=True)
        overdue=Invoice.objects.filter(due_date__lt=today).exclude(status__in=["PAID","CANCELLED"]).count()
        return Response({
            "active_subscriptions":active,
            "payments_received":received,
            "invoiced_total":invoiced,
            "outstanding_estimate":max(invoiced-received,0),
            "overdue_invoices":overdue,
        })
