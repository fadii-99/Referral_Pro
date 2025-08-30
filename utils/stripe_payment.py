import stripe
import os
from dotenv import load_dotenv
import stripe
from django.conf import settings
from utils.publishStripe import generate_token
from utils.secerteStripe import initiate_payment




def stripe_payment(card_number, exp_month, exp_year, cvc, price, plan_name, username):
    """Handle token generation and payment on the server side."""
    try:
        token = generate_token(card_number, exp_month, exp_year, cvc)
        payment_details = initiate_payment(float(price), token, plan_name, username)
        return payment_details, None
    except Exception as e:
        return False, str(e)
