from rest_framework import serializers
from ..models import Conversation, ConversationUsers
from accounts.serializers import UserSerializer

class ConversationUserSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ConversationUsers
        fields = ["user", "joined_at"]

class ConversationSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    is_group = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "title", "is_group", "created_at", "users"]

    def get_is_group(self, obj):
        return obj.conversation_users.count() > 2

    def get_users(self, obj):
        return ConversationUserSerializer(obj.conversation_users.all(), many=True).data