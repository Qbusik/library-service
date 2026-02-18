from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularRedocView,
    SpectacularSwaggerView,
    SpectacularAPIView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("user.urls", namespace="user")),
    path("", include("library_service.urls", namespace="core")),
    path("doc/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "doc/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("doc/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
