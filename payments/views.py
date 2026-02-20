from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from books.views import StandardPagination
from payments.models import Payment
from payments.serializers import PaymentListSerializer, PaymentDetailSerializer


class PaymentsViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = Payment.objects.select_related("borrowing")
        user = self.request.user

        if user.is_superuser:
            return queryset

        return queryset.filter(borrowing__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PaymentDetailSerializer
        return PaymentListSerializer
