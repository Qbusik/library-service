import datetime

from django.urls import reverse

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment


def test_correct_payment_created_with_borrow(auth_client, book_factory):
    book = Book.objects.create(
        title="TestBook",
        author="TestAuthor",
        cover=Book.Cover.HARD,
        inventory=10,
        daily_fee=1.50,
    )
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
