from django.db import models


class Cover(models.TextChoices):
    HARD = "HARD", "Hard cover"
    SOFT = "SOFT", "Soft cover"


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=4, choices=Cover.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=6, decimal_places=2)
