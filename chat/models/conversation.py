from django.db import models
from accounts.models import User

class Conversation(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')

    def __str__(self):
        return self.title or f"Conversation {self.id} | {self.user.firstname}"