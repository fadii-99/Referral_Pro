import stripe
from django.conf import settings



stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_payment_intent(amount, currency="usd", metadata=None):
    """
    Create a Stripe PaymentIntent and return the client secret.
    """
    intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),  # Stripe expects amount in cents
        currency=currency,
        metadata=metadata or {},
    )
    return intent.client_secret
