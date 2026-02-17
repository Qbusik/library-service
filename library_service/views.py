from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser

from library_service.models import Book
from library_service.serializers import BookListSerializer, BookDetailSerializer


class StandardPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookDetailSerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        return BookDetailSerializer

    def get_queryset(self):
        title = self.request.query_params.get("title")
        author = self.request.query_params.get("author")

        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)

        if author:
            queryset = queryset.filter(author__icontains=author)

        return queryset.distinct()
