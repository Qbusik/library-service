from django.urls import path, include
from rest_framework import routers

from library_service.views import BookViewSet

router = routers.DefaultRouter()
router.register("books", BookViewSet, basename="books")

app_name = "library_service"
urlpatterns = [
    path("", include(router.urls)),
]
