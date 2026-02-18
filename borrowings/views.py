from datetime import date

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from books.models import Book
from books.views import StandardPagination
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer, BorrowingDetailSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingListSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "create"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book")
        user = self.request.user

        if user.is_superuser:
            queryset = queryset

        elif user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)

        else:
            return queryset.none()

        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active.lower() in ("true", "1"):
            queryset = queryset.filter(actual_return_date__isnull=True)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingListSerializer

    def perform_create(self, serializer):
        book = serializer.validated_data["book"]

        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=book.pk)
            if book.inventory == 0:
                raise ValidationError("This book is not available.")
            book.inventory -= 1
            book.save()
            serializer.save(user=self.request.user)

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

        with transaction.atomic():
            borrowing.actual_return_date = date.today()
            borrowing.save()

            book = borrowing.book
            book.inventory += 1
            book.save()

        return Response(
            {"detail": f"Book '{book.title}' returned successfully."},
            status=status.HTTP_200_OK,
        )
