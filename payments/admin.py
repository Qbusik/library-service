from django.contrib import admin

from payments.models import Payment


class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "type",
        "money_to_pay",
        "borrowing",
    )


admin.site.register(Payment, PaymentAdmin)
