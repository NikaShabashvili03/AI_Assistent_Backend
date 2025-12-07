from datetime import timedelta
from django.utils import timezone
from .models import UserSubscription

def _duration_for_plan(plan):
    if plan.billing_cycle == "monthly":
        return timedelta(days=30)
    return timedelta(days=365)

def activate_subscription(user, plan, stripe_subscription_id=None, payment_intent_id=None):
    now = timezone.now()
    duration = _duration_for_plan(plan)

    try:
        sub = UserSubscription.objects.get(user=user, status="active")
        start = max(sub.end_date, now)
    except UserSubscription.DoesNotExist:
        start = now

    end = start + duration

    subscription, created = UserSubscription.objects.update_or_create(
        user=user,
        defaults={
            "plan": plan,
            "start_date": start,
            "end_date": end,
            "status": "active",
            "auto_renew": True,
            "stripe_subscription_id": stripe_subscription_id,
            "last_payment_intent": payment_intent_id,
        }
    )
    return subscription

def cancel_subscription(user):
    try:
        sub = UserSubscription.objects.get(user=user, status="active")
        sub.status = "cancelled"
        sub.auto_renew = False
        sub.save()
        return True
    except UserSubscription.DoesNotExist:
        return False

def has_active_subscription(user):
    try:
        sub = UserSubscription.objects.get(user=user, status="active")
        return sub.end_date > timezone.now()
    except UserSubscription.DoesNotExist:
        return False
