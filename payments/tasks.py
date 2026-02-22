import stripe
from celery import shared_task
from django.conf import settings
from payments.models import Payment
import logging

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10)
def check_expired_sessions(self):
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
            logger.warning(f"Stripe error for payment {payment.id}: {e}")

    if expired_ids:
        Payment.objects.filter(id__in=expired_ids).update(
            status=Payment.PaymentStatus.EXPIRED
        )
