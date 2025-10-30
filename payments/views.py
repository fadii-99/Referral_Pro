import json
import os
import uuid
from urllib.parse import urlencode

import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models

from .models import Withdrawal, EventAudit, IdempotencyKey, Liability

User = get_user_model()


stripe.api_key = os.getenv('STRIPE_SECRET_KEY') or settings.STRIPE_SECRET_KEY
STRIPE_CLIENT_ID = os.getenv('STRIPE_CONNECT_CLIENT_ID')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')


def test_page(request):
	return render(request, 'payments/test.html', {})


def connect_start(request):
	"""Redirect to Stripe OAuth authorize page.
	Query params:
	- role: 'company' or 'user' (who is connecting)
	- user_id: id of the user in our DB (for testing)
	- redirect_uri: optional override
	"""
	role = request.GET.get('role')
	user_id = request.GET.get('user_id')
	if not STRIPE_CLIENT_ID:
		return HttpResponseBadRequest('Missing STRIPE_CONNECT_CLIENT_ID')
	if not role or not user_id:
		return HttpResponseBadRequest('role and user_id required')

	redirect_uri = request.GET.get('redirect_uri') or request.build_absolute_uri('/payments/connect/stripe/callback/')
	state = json.dumps({'role': role, 'user_id': user_id})
	params = {
		'response_type': 'code',
		'client_id': STRIPE_CLIENT_ID,
		'scope': 'read_write',
		'redirect_uri': redirect_uri,
		'state': state,
	}
	url = f"https://connect.stripe.com/oauth/authorize?{urlencode(params)}"
	return HttpResponseRedirect(url)


def connect_callback(request):
	"""Handle Stripe OAuth callback and save connected account id to the user."""
	code = request.GET.get('code')
	error = request.GET.get('error')
	state_raw = request.GET.get('state')
	if error:
		return HttpResponseBadRequest(error)
	if not code or not state_raw:
		return HttpResponseBadRequest('Missing code/state')
	state = json.loads(state_raw)
	user_id = state.get('user_id')
	user = User.objects.filter(id=user_id).first()
	if not user:
		return HttpResponseBadRequest('User not found')

	resp = stripe.OAuth.token(grant_type='authorization_code', code=code)
	acct_id = resp.get('stripe_user_id')
	if not acct_id:
		return HttpResponseBadRequest('No account id in response')
	user.stripe_account_id = acct_id
	user.save(update_fields=['stripe_account_id'])
	return redirect('payments_test')


def create_account_link(request):
	"""Create an Account Link for onboarding a connected account (Express). Query: user_id"""
	user_id = request.GET.get('user_id')
	user = User.objects.filter(id=user_id).first()
	if not user or not user.stripe_account_id:
		return HttpResponseBadRequest('User or connected account missing')
	refresh = settings.STRIPE_CONNECT_REFRESH_URL
	return_url = settings.STRIPE_CONNECT_RETURN_URL
	link = stripe.AccountLink.create(
		account=user.stripe_account_id,
		type='account_onboarding',
		refresh_url=refresh,
		return_url=return_url,
	)
	return redirect(link.url)


@csrf_exempt
def create_withdrawal(request):
	"""POST { user_id, org_id, amount_cents } -> creates PI (Option 1), then transfer on webhook."""
	if request.method != 'POST':
		return HttpResponseBadRequest('POST only')
	data = json.loads(request.body.decode() or '{}')
	user_id = data.get('user_id')
	org_id = data.get('org_id')
	amount_cents = int(data.get('amount_cents') or 0)
	if not (user_id and org_id and amount_cents > 0):
		return HttpResponseBadRequest('user_id, org_id, amount_cents required')
	user = User.objects.filter(id=user_id).first()
	org = User.objects.filter(id=org_id).first()
	if not user or not org:
		return HttpResponseBadRequest('Invalid user/org')
	if not org.stripe_account_id:
		return HttpResponseBadRequest('Org not connected to Stripe')
	if not user.stripe_account_id:
		return HttpResponseBadRequest('User not connected to Stripe')

	# Minimal liability check (for demo)
	owed = Liability.objects.filter(org=org, user=user, state='open').aggregate(total=models.Sum('amount_cents'))['total'] or 0
	if owed < amount_cents:
		return HttpResponseBadRequest('Insufficient earmarked balance')

	transfer_group = f"wd_{uuid.uuid4().hex[:10]}"
	idemp = uuid.uuid4().hex
	Withdrawal.objects.create(
		org=org,
		user=user,
		amount_cents=amount_cents,
		state='requested',
		transfer_group=transfer_group,
		idempotency_key=idemp,
	)

	# Create PaymentIntent (Option 1) on platform, on_behalf_of = org account
	try:
		pi = stripe.PaymentIntent.create(
			amount=amount_cents,
			currency='usd',
			on_behalf_of=org.stripe_account_id,
			confirm=True,
			payment_method_types=['us_bank_account', 'card'],
			transfer_group=transfer_group,
			metadata={'org_id': str(org.id), 'user_id': str(user.id)},
			idempotency_key=idemp,
		)
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=400)

	Withdrawal.objects.filter(transfer_group=transfer_group).update(
		payment_intent_id=pi.id,
		state='debit_processing' if pi.status in ['processing', 'requires_capture', 'requires_action'] else 'authorized'
	)
	return JsonResponse({'payment_intent_id': pi.id, 'status': pi.status, 'transfer_group': transfer_group})


@csrf_exempt
def stripe_webhook(request):
	"""Handle Stripe events and progress Withdrawal states."""
	payload = request.body
	sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
	if not STRIPE_WEBHOOK_SECRET:
		return HttpResponseBadRequest('Missing STRIPE_WEBHOOK_SECRET')
	try:
		event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
	except Exception as e:
		return HttpResponse(status=400)

	# Idempotency per event
	audit, created = EventAudit.objects.get_or_create(
		event_id=event['id'],
		defaults={'event_type': event['type'], 'payload': event}
	)
	if not created:
		return HttpResponse(status=200)

	type_ = event['type']
	data = event['data']['object']

	if type_ in ('payment_intent.processing', 'payment_intent.succeeded', 'payment_intent.payment_failed'):
		pi = data
		transfer_group = pi.get('transfer_group')
		if not transfer_group:
			return HttpResponse(status=200)
		w = Withdrawal.objects.filter(transfer_group=transfer_group).first()
		if not w:
			return HttpResponse(status=200)
		if type_ == 'payment_intent.processing':
			w.state = 'debit_processing'
			w.save(update_fields=['state'])
		elif type_ == 'payment_intent.succeeded':
			w.state = 'debit_succeeded'
			w.save(update_fields=['state'])
			# Create transfer to user's connected account
			try:
				tr = stripe.Transfer.create(
					amount=w.amount_cents,
					currency='usd',
					destination=w.user.stripe_account_id,
					transfer_group=w.transfer_group,
					metadata={'withdrawal_id': str(w.id)}
				)
				w.transfer_id = tr.id
				w.state = 'transfer_created'
				w.save(update_fields=['transfer_id', 'state'])
			except Exception:
				w.state = 'transfer_failed'
				w.save(update_fields=['state'])
		elif type_ == 'payment_intent.payment_failed':
			w.state = 'payment_failed'
			w.save(update_fields=['state'])

	elif type_ in ('payout.paid', 'payout.failed'):
		payout = data
		# Try to link by metadata if present; otherwise, by searching recent withdrawals isn't trivial; skip association for demo
		pass

	return HttpResponse(status=200)
