import stripe
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.views import StandardPagination
from notifications.telegram import send_telegram_message
from borrowings.tasks import send_telegram_message_task
from payments.models import Payment
from payments.serializers import PaymentListSerializer, PaymentDetailSerializer
from payments.services import create_payment_session_for_payment


class PaymentsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoints for viewing payment records.

    Authenticated users can:
    - list and retrieve their own payments.

    Admin users can:
    - view all payments in the system.

    The view also provides Stripe-related redirect and utility endpoints:
    - success: called by Stripe after successful payment,
    - cancel: called when a user cancels the payment in Stripe Checkout,
    - renew: creates a new Stripe Checkout session for expired payments.
    """

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

    @extend_schema(
        description=(
            "Stripe redirect URL called after a successful Checkout payment. "
            "Verifies the Stripe session and marks the payment as PAID in the system."
        ),
        parameters=[
            OpenApiParameter(
                name="pk",
                description="ID of the payment",
                required=True,
                type=int,
            )
        ],
    )
    @action(detail=True, methods=["get"], url_path="success")
    def success(self, request, pk=None):
        payment = self.get_object()

        if payment.status == Payment.PaymentStatus.PAID:
            return Response(
                {
                    "detail": f"Payment for borrowing #{payment.borrowing.id} is already paid.",
                    "status": payment.status,
                }
            )

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

        message = (
            f"✅ Payment completed!\n"
            f"User: {payment.borrowing.user.email}\n"
            f"Book: {payment.borrowing.book.title}\n"
            f"Amount: {payment.money_to_pay} USD\n"
            f"Type: {payment.type}"
        )
        send_telegram_message_task.delay(message)

        return Response(
            {
                "detail": f"Payment for borrowing #{payment.borrowing.id} is successful.",
                "status": payment.status,
                "money_to_pay": payment.money_to_pay,
            }
        )

    @extend_schema(
        description=(
            "Stripe redirect URL called when the user cancels the Checkout payment. "
            "Does not change payment status, but returns the existing session URL "
            "so the user can retry payment later (Stripe sessions are valid ~24h)."
        ),
        parameters=[
            OpenApiParameter(
                name="pk",
                description="ID of the payment",
                required=True,
                type=int,
            )
        ],
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

    @extend_schema(
        description=(
            "API endpoint to renew an expired Stripe Checkout session. "
            "Creates a new Stripe session and updates session_id and session_url "
            "for the existing payment record."
        ),
        parameters=[
            OpenApiParameter(
                name="pk",
                description="ID of the payment",
                required=True,
                type=int,
            )
        ],
    )
    @action(detail=True, methods=["get"], url_path="renew")
    def renew(self, request, pk=None):
        payment = self.get_object()

        if payment.status == Payment.PaymentStatus.PAID:
            return Response(
                {"detail": "Payment is already completed.", "status": payment.status},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session_id, session_url = create_payment_session_for_payment(
                payment, request
            )
            return Response(
                {
                    "detail": "Payment session renewed successfully.",
                    "session_url": session_url,
                    "status": payment.status,
                    "money_to_pay": payment.money_to_pay,
                }
            )
        except Exception as e:
            raise ValidationError(f"Failed to renew payment session: {str(e)}")
