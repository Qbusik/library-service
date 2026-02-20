import datetime

from django.urls import reverse

from borrowings.models import Borrowing
from library_service_api.settings import FINE_MULTIPLIER
from payments.models import Payment


def test_correct_payment_created_with_borrow(auth_client, book_factory):
    book = book_factory()
    borrow_date = datetime.date.today().isoformat()
    return_date = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
    data = {
        "borrow_date": borrow_date,
        "expected_return_date": return_date,
        "book": book.id,
    }
    res = auth_client.post(
        reverse("borrowings:borrowings-list"), data=data, format="json"
    )
    assert res.status_code == 201

    borrowing = Borrowing.objects.get(id=res.data["id"])
    payment = Payment.objects.get(borrowing=borrowing)
    assert payment.status == Payment.PaymentStatus.PENDING
    assert payment.type == Payment.PaymentType.PAYMENT
    assert payment.money_to_pay == 15
    assert payment.session_id != ""
    assert payment.session_url != ""


def test_correct_payment_created_when_book_overdue(
    admin_client, borrowing_factory, book_factory
):
    book = book_factory(daily_fee=1.50)
    expected_return_date = (
        datetime.date.today() + datetime.timedelta(days=5)
    ).isoformat()
    actual_return_date = (
        datetime.date.today() + datetime.timedelta(days=8)
    ).isoformat()
    borrowing = borrowing_factory(book=book, expected_return_date=expected_return_date)

    res = admin_client.post(
        reverse(
            "borrowings:borrowings-return-book",
            kwargs={"pk": borrowing.id},
        ),
        data={"actual_return_date": actual_return_date},
    )
    assert res.status_code == 200

    payment = Payment.objects.get(borrowing=borrowing)
    assert payment.status == Payment.PaymentStatus.PENDING
    assert payment.type == Payment.PaymentType.FINE
    assert payment.money_to_pay == 4.50 * FINE_MULTIPLIER
    assert payment.session_id != ""
    assert payment.session_url != ""


def test_user_can_see_only_own_payments_admin_all(
    auth_client,
    admin_client,
    admin_user,
    sample_user,
    payment_factory,
    borrowing_factory,
):
    admin_borrowing = borrowing_factory(user=admin_user)
    user_borrowing = borrowing_factory(user=sample_user)
    payment_factory(borrowing=admin_borrowing)
    payment_factory(borrowing=user_borrowing)

    res = admin_client.get(reverse("payments:payments-list"))
    assert res.status_code == 200
    assert res.data["count"] == 2

    res = auth_client.get(reverse("payments:payments-list"))
    assert res.status_code == 200
    assert res.data["count"] == 1
