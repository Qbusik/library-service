from django.urls import path, include
from rest_framework import routers

from payments.views import PaymentsViewSet

router = routers.DefaultRouter()
router.register("payments", PaymentsViewSet, basename="payments")

app_name = "payments"

urlpatterns = [
    path("", include(router.urls)),
]
