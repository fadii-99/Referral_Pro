from django.db import models
from django.conf import settings


class IdempotencyKey(models.Model):
	key = models.CharField(max_length=200, unique=True)
	used_for = models.CharField(max_length=100)
	created_at = models.DateTimeField(auto_now_add=True)


class EventAudit(models.Model):
	event_id = models.CharField(max_length=200, unique=True)
	event_type = models.CharField(max_length=100)
	payload = models.JSONField()
	processed_at = models.DateTimeField(auto_now_add=True)
	is_duplicate = models.BooleanField(default=False)


class Liability(models.Model):
	STATE_CHOICES = [
		('open', 'Open'),
		('settled', 'Settled'),
	]
	org = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='org_liabilities')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_liabilities')
	amount_cents = models.PositiveIntegerField()
	state = models.CharField(max_length=20, choices=STATE_CHOICES, default='open')
	created_at = models.DateTimeField(auto_now_add=True)


class Withdrawal(models.Model):
	STATE_CHOICES = [
		('requested', 'requested'),
		('authorized', 'authorized'),
		('debit_processing', 'debit_processing'),
		('debit_succeeded', 'debit_succeeded'),
		('payment_failed', 'payment_failed'),
		('transfer_created', 'transfer_created'),
		('transfer_failed', 'transfer_failed'),
		('payout_paid', 'payout_paid'),
		('payout_failed', 'payout_failed'),
	]
	org = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='org_withdrawals')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_withdrawals')
	amount_cents = models.PositiveIntegerField()
	state = models.CharField(max_length=30, choices=STATE_CHOICES, default='requested')
	payment_intent_id = models.CharField(max_length=100, null=True, blank=True)
	transfer_id = models.CharField(max_length=100, null=True, blank=True)
	payout_id = models.CharField(max_length=100, null=True, blank=True)
	transfer_group = models.CharField(max_length=100, null=True, blank=True)
	idempotency_key = models.CharField(max_length=200, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		indexes = [
			models.Index(fields=['state']),
			models.Index(fields=['payment_intent_id']),
			models.Index(fields=['transfer_id']),
			models.Index(fields=['payout_id']),
		]
