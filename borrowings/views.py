from datetime import date

from django.db import transaction
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from books.models import Book
from books.views import StandardPagination
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingReturnSerializer,
)
from library_service_api.settings import FINE_MULTIPLIER
from notifications.telegram import send_telegram_message
from payments.models import Payment
from payments.services import create_payment_session_for_payment


class BorrowingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing book borrowings.

    Allows authenticated users to:
    - create new borrowings (rent books),
    - list and retrieve their own borrowings.

    Admin users can:
    - view all borrowings,
    - mark books as returned,
    - filter borrowings by user and activity status.

    Creating a borrowing automatically:
    - decreases book inventory,
    - calculates rental cost,
    - creates a Stripe payment session for the rental fee.

    Supports filtering by:
    - user_id (user ID, admin only),
    - actual_return_date (filter active or returned borrowings).
    """

    queryset = Borrowing.objects.all()
    serializer_class = BorrowingListSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "create"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        if self.action == "retrieve":
            queryset = Borrowing.objects.select_related("book")
        else:
            queryset = Borrowing.objects.all()
        user = self.request.user

        if user.is_superuser:
            pass

        elif user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)

        else:
            return queryset.none()

        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active and is_active.lower() in ("true", "1"):
            queryset = queryset.filter(actual_return_date__isnull=True)

        if is_active and is_active.lower() in ("false", "0"):
            queryset = queryset.filter(actual_return_date__isnull=False)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        if self.action == "return_book":
            return BorrowingReturnSerializer
        return BorrowingListSerializer

    def perform_create(self, serializer):
        book = serializer.validated_data["book"]

        borrow_start = serializer.validated_data["borrow_date"]
        borrow_end = serializer.validated_data["expected_return_date"]
        days = (borrow_end - borrow_start).days
        if days <= 0:
            raise ValidationError("Expected return date must be after borrow date.")
        money_to_pay = book.daily_fee * days

        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=book.pk)
            if book.inventory == 0:
                raise ValidationError("This book is not available.")
            book.inventory -= 1
            book.save()
            borrowing = serializer.save(user=self.request.user)

            payment = Payment.objects.create(
                status=Payment.PaymentStatus.PENDING,
                type=Payment.PaymentType.PAYMENT,
                borrowing=borrowing,
                session_url="",
                session_id="",
                money_to_pay=money_to_pay,
            )
            create_payment_session_for_payment(payment, self.request)

        try:
            send_telegram_message(
                f"New borrowing!\n"
                f"User: {self.request.user.email}\n"
                f"Book: {book.title}\n"
                f"From: {borrow_start}\n"
                f"To: {borrow_end}\n"
            )
        except Exception as e:
            print(f"Failed to send telegram notification: {e}")

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id",
                description="Filter borrowings by user ID (admin only).",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="is_active",
                description="Filter active borrowings. true = not returned, false = returned.",
                required=False,
                type=bool,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description=(
            "Admin endpoint to mark a borrowed book as returned. "
            "Updates the actual_return_date, increases book inventory, "
            "and automatically creates a Stripe payment session for overdue fines "
            "if the book is returned after the expected return date."
        )
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminUser],
        url_path="return",
    )
    def return_book(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "Book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return_date_str = request.data.get("actual_return_date")
        return_date = parse_date(return_date_str) if return_date_str else date.today()

        if return_date < borrowing.borrow_date:
            raise ValidationError("Return date cannot be before borrow date.")

        with transaction.atomic():
            borrowing.actual_return_date = return_date
            borrowing.save()

            book = borrowing.book
            book.inventory += 1
            book.save()

            if return_date > borrowing.expected_return_date:
                days_overdue = (return_date - borrowing.expected_return_date).days
                money_to_pay = book.daily_fee * days_overdue * FINE_MULTIPLIER
                payment = Payment.objects.create(
                    status=Payment.PaymentStatus.PENDING,
                    type=Payment.PaymentType.FINE,
                    borrowing=borrowing,
                    session_url="",
                    session_id="",
                    money_to_pay=money_to_pay,
                )
                create_payment_session_for_payment(payment, request)

        return Response(
            {
                "detail": f"Book '{book.title}' returned successfully.",
                "return_date": return_date,
            },
            status=status.HTTP_200_OK,
        )
