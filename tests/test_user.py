import pytest
from django.urls import reverse
from rest_framework import status

from tests.conftest import anon_client


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, expected_status",
    [
        (
            {
                "email": "",
                "first_name": "Test",
                "last_name": "Test",
                "password": "Test12345",
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            {
                "email": "test@test.com",
                "first_name": "Test",
                "last_name": "Test",
                "password": "1",
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            {
                "email": "test@test.com",
                "first_name": "",
                "last_name": "Test",
                "password": "Test12345",
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            {
                "email": "test@test.com",
                "first_name": "Test",
                "last_name": "",
                "password": "Test12345",
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            {
                "email": "test@test.com",
                "first_name": "Test",
                "last_name": "Test",
                "password": "Test12345",
            },
            status.HTTP_201_CREATED,
        ),
    ],
)
def test_user_create(anon_client, payload, expected_status):
    url = reverse("user:register")
    res = anon_client.post(url, data=payload, format="json")
    assert res.status_code == expected_status


@pytest.mark.django_db
def test_token_and_me_endpoint(anon_client):
    data = {
        "email": "test@test.com",
        "first_name": "TestUser",
        "last_name": "Test",
        "password": "Test12345",
    }
    res = anon_client.post(reverse("user:register"), data=data, format="json")
    assert res.status_code == status.HTTP_201_CREATED

    login_data = {"email": "test@test.com", "password": "Test12345"}
    login_res = anon_client.post(
        reverse("user:token_obtain_pair"), data=login_data, format="json"
    )
    assert login_res.status_code == status.HTTP_200_OK

    access_token = login_res.data["access"]
    anon_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    res = anon_client.get(reverse("user:manage"))
    assert res.status_code == 200
    assert res.data["email"] == "test@test.com"
    assert res.data["first_name"] == "TestUser"
