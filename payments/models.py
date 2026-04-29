from decimal import Decimal

from django.db import models

from borrowings.models import Borrowing


class Payment(models.Model):

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        EXPIRED = "EXPIRED", "Expired"

    class PaymentType(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(max_length=7, choices=PaymentStatus.choices)
    type = models.CharField(max_length=7, choices=PaymentType.choices)
    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payments"
    )
    session_url = models.URLField(max_length=500)
    session_id = models.TextField()
    money_to_pay = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        ordering = ["-status", "type"]

    def __str__(self):
        return f"Payment: {self.status} -> {self.type}"
