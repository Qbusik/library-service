from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularRedocView,
    SpectacularSwaggerView,
    SpectacularAPIView,
)
from rest_framework.permissions import AllowAny

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("user.urls", namespace="users")),
    path("api/", include("books.urls", namespace="books")),
    path("api/", include("borrowings.urls", namespace="borrowings")),
    path("api/", include("payments.urls", namespace="payments")),
    path(
        "doc/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"
    ),
    path(
        "doc/swagger/",
        SpectacularSwaggerView.as_view(
            url_name="schema", permission_classes=[AllowAny]
        ),
        name="swagger-ui",
    ),
    path(
        "doc/redoc/",
        SpectacularRedocView.as_view(url_name="schema", permission_classes=[AllowAny]),
        name="redoc",
    ),
]
