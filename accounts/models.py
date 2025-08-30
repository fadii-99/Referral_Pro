# accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


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
    image = models.ImageField(upload_to="profiles/", null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="solo")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"



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



# Subscriptions model
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    active_date = models.DateTimeField()
    expiry_date = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text='Duration in days')

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.active_date} to {self.expiry_date})"



# Transaction model
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")
    payment_method = models.CharField(max_length=20, default="stripe")
    payment_id = models.CharField(max_length=100, blank=True, null=True, help_text="Stripe charge ID or local bank reference")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} ({self.status}, {self.payment_method})"



# {'cardName': ['Usama Kamran'], 'cardNumber': ['0000000000000000'], 'expMonthValue': ['2025-11'], 'exp': ['11/25'], 'cvv': ['123'], 'profileType': ['company'], 'firstName': ['d'], 'lastName': ['d'], 'email': ['d'], 'companyName': ['d'], 'industry': ['Finance'], 'employees': ['1 – 50'], 'bizType': ['sole'], 'address1': ['1'], 'address2': ['1'], 'city': ['1'], 'postCode': ['1'], 'phone': ['1'], 'website': ['1'], 'usState': ['Arizona'], 'subscriptionBilling': ['monthly'], 'subscriptionPlanId': ['0'], 'subscriptionSeats': ['5'], 'paymentType': ['bank']}




