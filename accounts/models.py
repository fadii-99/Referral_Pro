# accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.core.files.storage import FileSystemStorage

# Import the custom storage
from utils.storage_backends import MediaStorage

media_storage = MediaStorage()

# SubscriptionPlan model
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    seats = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.seats} seats, ${self.price})"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            # for social logins (no password)
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("solo", "Solo"),
        ("rep", "Company Rep"),
        ("company", "Company"),
        ("superadmin", "Super Admin"),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # CHANGED: Update image field with custom storage and change upload_to path temporarily
    image = models.ImageField(upload_to="user_profiles/", storage=media_storage, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="solo")

    parent_company = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="employees",
        null=True,
        blank=True,
        limit_choices_to={"role": "company"},
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_passwordSet = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"

    def get_image_url(self):
        """Get the full S3 URL for the image"""
        if self.image:
            return self.image.url
        return None


# BusinessInfo model
class BusinessInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_info')
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100)
    employees = models.CharField(max_length=50)
    biz_type = models.CharField(max_length=50)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    post_code = models.CharField(max_length=20)
    website = models.CharField(max_length=255, blank=True, null=True)
    us_state = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.company_name} ({self.user.email})"


class OtpCode(models.Model):
    PURPOSES = [
        ("login", "Login"),
        ("reset_password", "Reset Password"),
        ("signup", "Signup"),
        ("verify_email", "Verify Email"),
        ("verify_phone", "Verify Phone"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50, choices=PURPOSES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.email} ({self.code}) - {self.purpose}"


class Subscription(models.Model):
    """
    Stores user subscription details with full management capabilities.
    """
    PLAN_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('trialing', 'Trialing'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan_name = models.CharField(max_length=100, default='Basic Plan')
    subscription_type = models.CharField(max_length=10, choices=PLAN_CHOICES, default='monthly')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Subscription limits and features
    seats_limit = models.PositiveIntegerField(default=1, help_text="Number of employees allowed")
    seats_used = models.PositiveIntegerField(default=0, help_text="Current number of employees")
    
    # Stripe subscription details
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Subscription timeline
    start_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan_name} ({self.status})"
    
    def is_active(self):
        """Check if subscription is currently active"""
        from django.utils import timezone
        return (
            self.status == 'active' and 
            self.current_period_end and
            self.current_period_end > timezone.now()
        )
    
    def is_expired(self):
        """Check if subscription has expired"""
        from django.utils import timezone
        return (
            self.current_period_end and 
            self.current_period_end < timezone.now()
        )
    
    def can_add_employee(self):
        """Check if can add more employees within seat limits"""
        return self.seats_used < self.seats_limit
    
    def days_until_expiry(self):
        """Get days until subscription expires"""
        from django.utils import timezone
        if self.current_period_end and self.current_period_end > timezone.now():
            delta = self.current_period_end - timezone.now()
            return delta.days
        return 0


class Transaction(models.Model):
    """
    Comprehensive payment transaction records with all Stripe details.
    """
    TRANSACTION_TYPES = [
        ('subscription', 'Subscription Payment'),
        ('one_time', 'One-time Payment'),
        ('refund', 'Refund'),
        ('upgrade', 'Plan Upgrade'),
        ('downgrade', 'Plan Downgrade'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('requires_action', 'Requires Action'),
        ('requires_confirmation', 'Requires Confirmation'),
        ('requires_payment_method', 'Requires Payment Method'),
        ('processing', 'Processing'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='subscription')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    
    # Payment method details
    payment_method = models.CharField(max_length=20, default="stripe")
    payment_method_type = models.CharField(max_length=50, blank=True, null=True, help_text="card, bank_transfer, etc.")
    card_brand = models.CharField(max_length=20, blank=True, null=True, help_text="visa, mastercard, etc.")
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_exp_month = models.CharField(max_length=2, blank=True, null=True)
    card_exp_year = models.CharField(max_length=4, blank=True, null=True)
    
    # Stripe IDs for reference and management
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_invoice_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Additional transaction info
    receipt_email = models.EmailField(blank=True, null=True)
    receipt_url = models.URLField(blank=True, null=True)
    failure_code = models.CharField(max_length=100, blank=True, null=True)
    failure_message = models.TextField(blank=True, null=True)
    
    # Refund details
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    refund_reason = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    stripe_created_at = models.DateTimeField(null=True, blank=True, help_text="Transaction timestamp from Stripe")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - ${self.amount} ({self.status}) - {self.transaction_type}"
    
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == 'succeeded'
    
    def is_refundable(self):
        """Check if transaction can be refunded"""
        return (
            self.status == 'succeeded' and 
            self.refunded_amount < self.amount and
            self.transaction_type not in ['refund']
        )




