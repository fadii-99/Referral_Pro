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
        
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            # Get old status for existing objects
            old_instance = Referral.objects.get(pk=self.pk)
            old_status = old_instance.status
        
        super().save(*args, **kwargs)
        
        # Handle reward logic after saving
        if is_new:
            # New referral created - create pending reward
            self._create_pending_reward()
        elif old_status and old_status != self.status:
            # Status changed - update reward accordingly
            self._handle_status_change(old_status)

    def _create_pending_reward(self):
        """Create a pending reward when referral is first created"""
        try:
            ReferralReward.objects.create(
                referral=self,
                user=self.referred_by,
                points_awarded=100,
                reason=f"Referral {self.reference_id} created",
                status="pending"
            )
        except Exception as e:
            print(f"Error creating pending reward: {str(e)}")

    def _handle_status_change(self, old_status):
        """Handle reward updates when referral status changes"""
        try:
            reward = ReferralReward.objects.filter(referral=self).first()
            
            if self.status == "completed" and old_status != "completed":
                # Referral completed - update reward status and give points
                if reward:
                    reward.status = "completed"
                    reward.reason = f"Referral {self.reference_id} completed"
                    reward.save()
                    
                    # Add points to user if they have a points field
                    if hasattr(self.referred_by, 'points'):
                        self.referred_by.points += reward.points_awarded
                        self.referred_by.save()
                    
                    self.reward_given = True
                    Referral.objects.filter(pk=self.pk).update(reward_given=True)
                    
            elif self.status == "cancelled":
                # Referral cancelled - remove reward record
                if reward:
                    reward.delete()
                    self.reward_given = False
                    Referral.objects.filter(pk=self.pk).update(reward_given=False)
                    
        except Exception as e:
            print(f"Error handling status change: {str(e)}")

    def _give_reward(self):
        """Legacy method - kept for backward compatibility"""
        self._handle_status_change("pending")



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
    status = models.CharField(max_length=50, default="pending")
    withdrawal_status = models.BooleanField(default=False)
    awarded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.points_awarded} points to {self.user.email} for {self.referral.reference_id}"


