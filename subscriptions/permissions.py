from rest_framework.permissions import BasePermission
from django.utils import timezone
from .models import UserSubscription

class HasActiveSubscription(BasePermission):
    message = "You must have an active subscription to access this resource."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            sub = UserSubscription.objects.get(user=user, status="active")
            return sub.end_date > timezone.now()
        except UserSubscription.DoesNotExist:
            return False
