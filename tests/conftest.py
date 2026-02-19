import datetime
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing


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


@pytest.fixture
def book_factory(db):
    def create(**params):
        defaults = {
            "title": "Test-book",
            "author": "Test-author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": 1.50,
        }
        defaults.update(params)
        return Book.objects.create(**defaults)

    return create


@pytest.fixture
def borrowing_factory(db, book_factory, sample_user):
    def create(**params):
        book = params.pop("book", book_factory())
        user = params.pop("user", sample_user)
        defaults = {
            "borrow_date": datetime.date.today(),
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=10),
            "book": book,
            "user": user,
        }
        defaults.update(params)
        return Borrowing.objects.create(**defaults)

    return create
