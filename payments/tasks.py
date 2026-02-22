import stripe
from celery import shared_task
from django.conf import settings
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10)
def check_expired_sessions(self):
    print("RUNNING: check_expired_sessions")
    payments = Payment.objects.filter(
        status=Payment.PaymentStatus.PENDING,
        type=Payment.PaymentType.PAYMENT,
    ).only("id", "session_id")

    expired_ids = []

    for payment in payments:
        try:
            session = stripe.checkout.Session.retrieve(payment.session_id)

            if session.status == "expired":
                expired_ids.append(payment.id)

        except stripe.error.StripeError as e:
            print(f"Stripe error for payment {payment.id}: {e}")

    if expired_ids:
        Payment.objects.filter(id__in=expired_ids).update(
            status=Payment.PaymentStatus.EXPIRED
        )
