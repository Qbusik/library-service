from decimal import Decimal

from django.db import models

from user.models import User


class Cover(models.TextChoices):
    HARD = "HARD", "Hard cover"
    SOFT = "SOFT", "Soft cover"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PAID = "PAID", "Paid"


class PaymentType(models.TextChoices):
    PAYMENT = "PAYMENT", "Payment"
    FINE = "FINE", "Fine"


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=4, choices=Cover.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} - {self.author}"


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


class Payment(models.Model):
    status = models.CharField(max_length=7, choices=PaymentStatus.choices)
    type = models.CharField(max_length=7, choices=PaymentType.choices)
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE)
    session_url = models.URLField()
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        ordering = ["status", "type"]

    def __str__(self):
        return f"Payment: {self.status} -> {self.type}"
