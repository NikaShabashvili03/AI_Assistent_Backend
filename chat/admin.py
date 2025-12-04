from django.contrib import admin
from .models import Conversation, ConversationUsers, Message, Blog

class ConversationUsersInline(admin.TabularInline):
    model = ConversationUsers
    extra = 1

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'user_list')
    inlines = [ConversationUsersInline]

    def user_list(self, obj):
        return ", ".join([cu.user.firstname for cu in obj.conversation_users.all()])
    user_list.short_description = "Users"

admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message)
admin.site.register(Blog)
