import stripe
from dotenv import load_dotenv
import os
load_dotenv()  

def generate_token(card_number, expiration_month, expiration_year, cvv):
    # stripe.api_key = 'pk_test_51PQ6OP04AHp8Ze31p9kq5MITO4zGVr1sxlhcr1zzMBORj1bvN0oABtAlbdd6akjRAvJRA6y0uRazJJNZ2gOHAwMd00qcZwQrN4'
    stripe.api_key = os.environ["STRIPE_PUBLISHABLE_KEY"]
    token_response = stripe.Token.create(
            card={
                'number': card_number,
                'exp_month': expiration_month,
                'exp_year': expiration_year,
                'cvc': cvv
            }
        )
    tokenId = token_response['id']


    return tokenId