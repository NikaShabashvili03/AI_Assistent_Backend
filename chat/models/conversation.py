from django.db import models
from accounts.models import User
from chat.models.assistant import Assistant

class Conversation(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    
    def __str__(self):
        return self.title or f"Conversation {self.id} | {self.user.firstname}"
    
class ConversationAssistant(models.Model):
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name='conversations')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='assistants')

    def __str__(self):
        return f"{self.assistant.name} | {self.conversation.title}"