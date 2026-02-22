import datetime
import pytest
from django.urls import reverse
from rest_framework import status

from payments.models import Payment
from tests.conftest import borrowing_factory, auth_client


@pytest.mark.django_db
class TestUnauthorizedUser:
    def test_unauthorized_user_cant_access_borrowings(self, anon_client):
        res = anon_client.get(reverse("borrowings:borrowings-list"))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        res = anon_client.post(reverse("borrowings:borrowings-list"))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        res = anon_client.get(reverse("borrowings:borrowings-detail", kwargs={"pk": 1}))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAuthorizedUser:
    def test_authorized_user_can_create_and_see_own_borrowings(
        self, auth_client, book_factory, borrowing_factory, another_user
    ):
        book = book_factory()
        borrowing = borrowing_factory(book=book, user=another_user)
        res = auth_client.get(reverse("borrowings:borrowings-list"))
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 0
        data = {
            "borrow_date": borrowing.expected_return_date,
            "expected_return_date": borrowing.borrow_date,
            "book": book.id,
        }
        res = auth_client.post(
            reverse("borrowings:borrowings-list"),
            data=data,
            format="json",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        data = {
            "borrow_date": borrowing.borrow_date,
            "expected_return_date": borrowing.expected_return_date,
            "book": book.id,
        }
        res = auth_client.post(
            reverse("borrowings:borrowings-list"),
            data=data,
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        res = auth_client.get(reverse("borrowings:borrowings-list"))
        assert res.data["count"] == 1

    def test_authorized_user_can_see_detail_of_only_own_borrowings(
        self, auth_client, borrowing_factory, sample_user, another_user
    ):
        borrowing_factory(user=another_user)
        borrowing_factory(user=sample_user)
        res = auth_client.get(reverse("borrowings:borrowings-detail", kwargs={"pk": 1}))
        assert res.status_code == status.HTTP_404_NOT_FOUND
        res = auth_client.get(reverse("borrowings:borrowings-detail", kwargs={"pk": 2}))
        assert res.status_code == status.HTTP_200_OK

    def test_authorized_user_cant_return_book_by_him_self(
        self, borrowing_factory, sample_user, auth_client
    ):
        borrowing = borrowing_factory(user=sample_user)
        url = reverse("borrowings:borrowings-return-book", kwargs={"pk": borrowing.id})
        return_date = (datetime.date.today() + datetime.timedelta(days=20)).isoformat()
        res = auth_client.post(url, {"actual_return_date": return_date}, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cant_borrow_when_has_unpaid_payments(
        self, book_factory, borrowing_factory, auth_client, sample_user
    ):
        book = book_factory()
        borrowing = borrowing_factory()
        payment = Payment.objects.create(
            type=Payment.PaymentType.PAYMENT,
            status=Payment.PaymentStatus.PENDING,
            borrowing=borrowing,
            session_url="",
            session_id="",
            money_to_pay=10.00,
        )
        data = {
            "borrow_date": borrowing.borrow_date,
            "expected_return_date": borrowing.expected_return_date,
            "book": book.id,
        }
        res = auth_client.post(
            reverse("borrowings:borrowings-list"),
            data=data,
            format="json",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        payment.status = Payment.PaymentStatus.PAID
        payment.save()
        res = auth_client.post(
            reverse("borrowings:borrowings-list"),
            data=data,
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestAdminUser:
    def test_admin_user_can_return_book_and_validate_return_date(
        self, borrowing_factory, admin_client
    ):
        borrowing = borrowing_factory()
        url = reverse("borrowings:borrowings-return-book", kwargs={"pk": borrowing.id})
        return_date = (datetime.date.today() - datetime.timedelta(days=20)).isoformat()
        res = admin_client.post(url, {"actual_return_date": return_date}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        return_date = (datetime.date.today() + datetime.timedelta(days=20)).isoformat()
        res = admin_client.post(url, {"actual_return_date": return_date}, format="json")
        assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestBookInventoryInBorrowing:
    def test_book_inventory_when_borrowing_and_returning(
        self, book_factory, borrowing_factory, auth_client, admin_client
    ):
        book = book_factory(inventory=1)
        data = {
            "borrow_date": datetime.date.today().isoformat(),
            "expected_return_date": (
                datetime.date.today() + datetime.timedelta(days=20)
            ).isoformat(),
            "book": book.id,
        }
        res = auth_client.post(
            reverse("borrowings:borrowings-list"),
            data=data,
            format="json",
        )
        book.refresh_from_db()
        assert res.status_code == status.HTTP_201_CREATED
        assert book.inventory == 0

        res = auth_client.post(
            reverse("borrowings:borrowings-list"),
            data=data,
            format="json",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        url = reverse("borrowings:borrowings-return-book", kwargs={"pk": 1})
        return_date = (datetime.date.today() + datetime.timedelta(days=20)).isoformat()
        admin_client.post(url, {"actual_return_date": return_date}, format="json")
        book.refresh_from_db()
        assert book.inventory == 1
