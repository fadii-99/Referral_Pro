import stripe
from dotenv import load_dotenv
import os
load_dotenv() 

def initiate_payment(total_payment, tokenId, plan_name, username):
    # stripe.api_key = 'sk_test_51PQ6OP04AHp8Ze31SFhdISvLLtIA896V7GK9c83wsBOQwKkmHXO8a7bDbsxJvlaUpd8iZdSWIRIzKB7duyvxxINa00Z9Ymxwef'
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

    token = stripe.Token.retrieve(tokenId)

    card = token['card']

    card_brand = card['brand']

    payment = stripe.Charge.create(
            amount= int(total_payment)*100,         
            currency='usd',
            description=f"{plan_name} paid by {username} with amount {int(total_payment) * 100} cents",
            source=tokenId,
            )
    if payment['paid']:
        charge_id = payment.get("id")
        receipt_url = payment.get("receipt_url")
        card_id = payment.get("source", {}).get("id")
        return {
            "charge_id": charge_id,
            "receipt_url": receipt_url,
            "card_id": card_id
        }
    else:
        return False


def identify_card_type(token_id):
    stripe.api_key = 'sk_test_51PQ6OP04AHp8Ze31SFhdISvLLtIA896V7GK9c83wsBOQwKkmHXO8a7bDbsxJvlaUpd8iZdSWIRIzKB7duyvxxINa00Z9Ymxwef'

    token = stripe.Token.retrieve(token_id)

    card = token['card']

    card_brand = card['brand']

    if 'funding' in card:
        card_funding = card['funding']
        card_type = f"{card_brand} {card_funding.capitalize()}"
    else:
        card_type = f"{card_brand} (type not determined)"
    
    return card_type