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
        return Borrowing.objects.filter(user=self.request.user).select_related("book")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingListSerializer
