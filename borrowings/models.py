from django.db import models

from books.models import Book
from user.models import User


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField()
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-borrow_date"]

    def __str__(self):
        return f"Borrow: {self.borrow_date} -> {self.expected_return_date}"
