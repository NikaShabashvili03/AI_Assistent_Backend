from django.db import models
from accounts.models import User

class Conversation(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Conversation {self.id}"
    
class ConversationUsers(models.Model):
    conversation = models.ForeignKey(
        Conversation, related_name="conversation_users", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="user_conversations", on_delete=models.CASCADE
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("conversation", "user") 

    def __str__(self):
        return f"{self.user.firstname} in {self.conversation}"