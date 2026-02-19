from django.urls import reverse
from rest_framework import status

from borrowings.models import Borrowing


class TestUnauthorizedUser:
    def test_unauthorized_user_cant_access_borrowings(self, anon_client):
        Borrowing.objects.create()

        res = anon_client.get(reverse("borrowings:borrowings-list"))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthorizedUser:
    pass


class TestAdminUser:
    pass
