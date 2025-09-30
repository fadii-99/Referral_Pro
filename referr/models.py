from django.db import models
from accounts.models import User
import uuid


class Referral(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("friend_opted_in", "Friend Opted In"),
        ("business_accepted", "Business Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    reference_id = models.CharField(
        max_length=20, unique=True, editable=False, default=""
    )
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

    service_type = models.TextField(blank=True, null=True)
    urgency = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    privacy_opted = models.BooleanField(default=False)
    permission_consent = models.BooleanField(default=False)


    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    referred_by_approval = models.BooleanField(default=False)
    company_approval = models.BooleanField(default=False)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reward_given = models.BooleanField(default=False)   # ✅ Added field

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Referral {self.reference_id} from {self.referred_by.email} to {self.referred_to.email} ({self.company.company_name})"

    def save(self, *args, **kwargs):
        # Generate reference_id if not exists
        if not self.reference_id:
            self.reference_id = f"REF-{uuid.uuid4().hex[:8].upper()}"
        
        # Check if status changed to completed and reward not given yet
        if self.pk:  # Only for existing objects
            old_instance = Referral.objects.get(pk=self.pk)
            if (old_instance.status != "completed" and 
                self.status == "completed" and 
                not self.reward_given):
                self._give_reward()
        
        super().save(*args, **kwargs)

    def _give_reward(self):
        """Give 100 points reward to the referred_by user"""
        try:
            if hasattr(self.referred_by, 'points'):
                self.referred_by.points += 100
                self.referred_by.save()
            
            self.reward_given = True   # ✅ will now work
            self.save(update_fields=["reward_given"])

            ReferralReward.objects.create(
                referral=self,
                user=self.referred_by,
                points_awarded=100,
                reason=f"Referral {self.reference_id} completed"
            )
        except Exception as e:
            print(f"Error giving reward: {str(e)}")



class ReferralAssignment(models.Model):
    referral = models.ForeignKey(
        Referral,
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_referrals",
        null=True, blank=True
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
   

class ReferralReward(models.Model):
    """Track referral rewards given to users"""
    referral = models.OneToOneField(
        Referral,
        on_delete=models.CASCADE,
        related_name="reward_record"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="referral_rewards"
    )
    points_awarded = models.IntegerField(default=100)
    reason = models.CharField(max_length=255)
    awarded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.points_awarded} points to {self.user.email} for {self.referral.reference_id}"


