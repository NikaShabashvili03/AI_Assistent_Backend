from rest_framework import permissions
from ..models import ConversationUsers

class IsConversationOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not obj.is_group:
            return False

        try:
            cu = ConversationUsers.objects.get(conversation=obj, user=request.user)
            return cu.role in ["owner", "admin"]
        except ConversationUsers.DoesNotExist:
            return False

class IsConversationOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        try:
            cu = ConversationUsers.objects.get(conversation=obj, user=request.user)
            return cu.role == "owner"
        except ConversationUsers.DoesNotExist:
            return False

class IsGroupConversation(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.is_group