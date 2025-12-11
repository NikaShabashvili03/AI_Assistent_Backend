from django.db import models
from accounts.models import User

class Conversation(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_group = models.BooleanField(default=False)

    def __str__(self):
        return self.title or f"Conversation {self.id}"

    @property
    def member_count(self):
        return self.conversation_users.count()
            
class ConversationUsers(models.Model):
    ROLE_CHOICES = (
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
    )

    conversation = models.ForeignKey(
        Conversation, related_name="conversation_users", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="user_conversations", on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="member"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("conversation", "user")

    def __str__(self):
        return f"{self.user.firstname} ({self.role}) in {self.conversation}"