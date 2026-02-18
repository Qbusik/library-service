from datetime import date

from django.core.exceptions import ValidationError
from django.db import models

from books.models import Book
from user.models import User


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-borrow_date"]

    def __str__(self):
        return f"Borrow: {self.borrow_date} -> {self.expected_return_date}"

    def clean(self):
        if self.borrow_date < date.today():
            raise ValidationError({"borrow_date": "Borrow date cannot be in the past."})

        if self.expected_return_date <= self.borrow_date:
            raise ValidationError(
                {
                    "expected_return_date": "Expected return date must be after borrow date."
                }
            )
