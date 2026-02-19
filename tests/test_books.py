import pytest
from django.urls import reverse
from rest_framework import status


def test_only_admin_can_create_and_modify_books(auth_client, admin_client):
    data = {
        "title": "Test",
        "author": "Test-Author",
        "cover": "HARD",
        "inventory": 10,
        "daily_fee": 1.20,
    }
    res = auth_client.post(reverse("books:books-list"), data=data, format="json")
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = admin_client.post(reverse("books:books-list"), data=data, format="json")
    assert res.status_code == status.HTTP_201_CREATED
    book_id = res.data["id"]

    patch_data = {"inventory": 120}

    res = auth_client.patch(
        reverse("books:books-detail", args=[book_id]), data=patch_data, format="json"
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN
    res = admin_client.patch(
        reverse("books:books-detail", args=[book_id]), data=patch_data, format="json"
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.data["inventory"] == 120


@pytest.mark.django_db
def test_unauthenticated_user_can_view_books(anon_client, book_factory):
    book_factory()
    res = anon_client.get(reverse("books:books-list"))
    assert res.status_code == status.HTTP_200_OK
    assert res.data["count"] == 1
