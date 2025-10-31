from django.contrib import admin
from .models import Conversation, Message, Assistant, AssistantTags, ConversationAssistant

class ConversationAssistantInline(admin.TabularInline):
    model = ConversationAssistant
    extra = 1

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'created_at']
    inlines = [ConversationAssistantInline]

admin.site.register(Message)
admin.site.register(AssistantTags)
admin.site.register(Assistant)