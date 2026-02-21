import stripe
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.views import StandardPagination
from notifications.telegram import send_telegram_message
from payments.models import Payment
from payments.serializers import PaymentListSerializer, PaymentDetailSerializer


class PaymentsViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = Payment.objects.select_related(
            "borrowing", "borrowing__book", "borrowing__user"
        )
        user = self.request.user

        if user.is_superuser:
            return queryset

        return queryset.filter(borrowing__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PaymentDetailSerializer
        return PaymentListSerializer

    @action(detail=True, methods=["get"], url_path="success")
    def success(self, request, pk=None):
        payment = self.get_object()

        session_id = request.GET.get("session_id")
        if not session_id:
            return Response(
                {"detail": "No session_id provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                payment.status = Payment.PaymentStatus.PAID
                payment.save()
        except stripe.error.StripeError:
            return Response(
                {"detail": "Could not verify payment with Stripe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            send_telegram_message(
                f"✅ Payment completed!\n"
                f"User: {payment.borrowing.user.email}\n"
                f"Book: {payment.borrowing.book.title}\n"
                f"Amount: {payment.money_to_pay} USD\n"
                f"Type: {payment.type}"
            )
        except Exception as e:
            print(f"Failed to send telegram notification: {e}")

        return Response(
            {
                "detail": f"Payment for borrowing #{payment.borrowing.id} is successful.",
                "status": payment.status,
                "money_to_pay": payment.money_to_pay,
            }
        )

    @action(detail=True, methods=["get"], url_path="cancel")
    def cancel(self, request, pk=None):
        payment = self.get_object()
        return Response(
            {
                "detail": f"Payment for borrowing #{payment.borrowing.id} was canceled. You can pay later using the same session (valid 24h).",
                "status": payment.status,
                "money_to_pay": payment.money_to_pay,
                "session_url": payment.session_url,
            }
        )
