from django.db import models
from accounts.models import User



class Referral(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("friend_opted_in", "Friend Opted In"),
        ("business_accepted", "Business Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    referred_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="referrals_made"
    )
    referred_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="referrals_received"
    )
    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="referrals"
    )

    service_type = models.CharField(max_length=100, blank=True, null=True)
    urgency = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    privacy_opted = models.BooleanField(default=False)
    permission_concent = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Referral {self.id} from {self.referred_by.email} to {self.referred_to.email} ({self.company.company_name})"
