from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from books.views import StandardPagination
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer, BorrowingDetailSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingListSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ("POST", "GET"):
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book")

        if self.request.user.is_superuser:
            return queryset

        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user).select_related("book")

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingListSerializer
