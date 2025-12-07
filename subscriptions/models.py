from django.db import models

from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import User

class SubscriptionPlan(models.Model):
    BILLING_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CHOICES)
    active = models.BooleanField(default=True)

    stripe_price_id = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.billing_cycle})"


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    auto_renew = models.BooleanField(default=True)

    stripe_subscription_id = models.CharField(max_length=200, blank=True, null=True)
    last_payment_intent = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        return self.status == "active" and self.end_date > timezone.now()

    def __str__(self):
        return f"{getattr(self.user, 'email', str(self.user))} -> {self.plan.name}"
