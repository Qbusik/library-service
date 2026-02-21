from celery import shared_task
from datetime import date
from borrowings.models import Borrowing
from notifications.telegram import send_telegram_message


@shared_task
def check_overdue_borrowings():
    today = date.today()
    overdue_books = Borrowing.objects.filter(
        expected_return_date__lte=today, actual_return_date__isnull=True
    ).select_related("book", "user")

    if not overdue_books.exists():
        send_telegram_message("✅ No borrowings overdue for today!")
        return

    for borrowing in overdue_books:
        send_telegram_message(
            f"Overdue borrowing!\n"
            f"User: {borrowing.user.username}\n"
            f"Book: {borrowing.book.title}\n"
            f"Expected return date: {borrowing.expected_return_date.strftime('%Y-%m-%d')}"
        )
