from decimal import Decimal

import stripe
from django.conf import settings
from django.urls import reverse

from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_session_for_payment(payment: Payment, request):
    if not payment:
        raise ValueError("Payment is required")

    amount_cents = int((payment.money_to_pay * Decimal("100")).quantize(Decimal("1")))

    success_url = (
        request.build_absolute_uri(
            reverse("payments:payments-success", args=[payment.id])
        )
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = request.build_absolute_uri(
        reverse("payments:payments-cancel", args=[payment.id])
    )

    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("Stripe secret key is not set")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{payment.type} for borrowing #{payment.borrowing.id} -> {payment.borrowing.book.title}"
                    },
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    payment.session_id = session.id
    payment.session_url = session.url
    payment.status = Payment.PaymentStatus.PENDING
    payment.save()

    return session.id, session.url
