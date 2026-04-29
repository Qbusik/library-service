from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, AllowAny, SAFE_METHODS

from books.models import Book
from books.serializers import BookListSerializer, BookDetailSerializer


class StandardPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class BookViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing books in the library catalog.

    All users can:
    - list all books,
    - retrieve book details.

    Admin users can:
    - create new books,
    - update existing books,
    - delete books.

    Supports filtering by:
    - title (case-insensitive, partial match),
    - author (case-insensitive, partial match).
    """
    queryset = Book.objects.all()
    serializer_class = BookDetailSerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="title",
                description="Filter books by title (case-insensitive, partial match).",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="author",
                description="Filter books by author (case-insensitive, partial match).",
                required=False,
                type=str,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
