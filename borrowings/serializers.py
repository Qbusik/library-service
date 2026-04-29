from rest_framework import serializers

from books.serializers import BookDetailSerializer
from borrowings.models import Borrowing
from payments.models import Payment


class BorrowingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "user",
        )
        read_only_fields = ("actual_return_date", "user")

    def validate(self, attrs):
        user = self.context["request"].user
        unpaid_payments = Payment.objects.filter(
            borrowing__user=user,
            status__in=[
                Payment.PaymentStatus.PENDING,
                Payment.PaymentStatus.EXPIRED,
            ],
        )

        if unpaid_payments.exists():
            raise serializers.ValidationError(
                "You have unpaid payments and cannot borrow a new book."
            )

        instance = Borrowing(**attrs)
        instance.clean()
        return attrs


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookDetailSerializer()

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "borrow_date", "expected_return_date", "actual_return_date")
        read_only_fields = ("borrow_date", "expected_return_date")
