from rest_framework import serializers

from books.serializers import BookDetailSerializer
from borrowings.models import Borrowing


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
