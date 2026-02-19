import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def sample_user(db):
    return get_user_model().objects.create_user(
        email="user@test.com", password="password123"
    )


@pytest.fixture
def another_user(db):
    return get_user_model().objects.create_user(
        email="user2@test.com", password="password123"
    )


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser(
        email="admin@admin.com", password="admin123"
    )


@pytest.fixture
def auth_client(sample_user):
    client = APIClient()
    client.force_authenticate(sample_user)
    return client


@pytest.fixture
def anon_client():
    client = APIClient()
    return client


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    return client
