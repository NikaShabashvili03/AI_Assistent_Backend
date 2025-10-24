# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Conversation, Message
from .serializers import ConversationSerializer
from .utils.ollama import ask_ollama

@receiver(post_save, sender=Message)
def update_conversation_title_on_first_assistant_message(sender, instance, created, **kwargs):
    if not created:
        return 

    conversation = instance.conversation

    if instance.role == 'assistant':
        has_other_assistant_msgs = conversation.messages.filter(role='assistant').exclude(id=instance.id).exists()
        if not has_other_assistant_msgs:
            prompt_text = (
                f"Generate a concise and descriptive title for a conversation based on the following message:\n"
                f"{instance.content}\n" 
                f"Keep it under 10 characters, clear, catchy and only one option."
            )

            try:
                generated_title = ask_ollama(prompt_text)
                conversation.title = generated_title[:100] if generated_title else instance.content[:100]
            except Exception:
                conversation.title = instance.content[:100]

            conversation.save(update_fields=['title'])

@receiver(post_save, sender=Conversation)
def conversation_update(sender, instance, created, **kwargs):
    if created:
        return
    
    channel_layer = get_channel_layer()
    group_name = f"conversations_{instance.user.id}"

    data = {
        "type": "send_conversation_update",
        "data": ConversationSerializer(instance).data
    }

    async_to_sync(channel_layer.group_send)(group_name, data)


# @receiver(post_delete, sender=Conversation)
# def conversation_deleted(sender, instance, **kwargs):
#     channel_layer = get_channel_layer()
#     group_name = f"conversations_{instance.user.id}"

#     data = {
#         "type": "send_conversation_delete",
#         "data": {"id": instance.id}
#     }

#     async_to_sync(channel_layer.group_send)(group_name, data)
