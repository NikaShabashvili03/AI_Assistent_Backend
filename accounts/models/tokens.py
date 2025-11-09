from django.db import models
from django.utils import timezone
from accounts.models import User


class TokenPlan(models.Model):
    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
        ("enterprise", "Enterprise"),
    ]

    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    daily_limit = models.PositiveIntegerField(help_text="Max tokens per day for this plan")

    def __str__(self):
        return f"{self.get_name_display()} ({self.daily_limit} tokens/day)"


class UserTokenUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="token_usage")
    date = models.DateField(default=timezone.now)
    used_tokens = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.firstname} - {self.date} ({self.used_tokens} tokens)"
