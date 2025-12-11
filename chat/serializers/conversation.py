from rest_framework import serializers
from ..models import Conversation, ConversationUsers
from accounts.serializers import UserSerializer
from accounts.models import User

class ConversationUserSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ConversationUsers
        fields = ["user", "joined_at", "role"]

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

class ConversationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    users = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        write_only=True
    )

    def validate_users(self, user_ids):
        user_ids = list(set(user_ids))

        valid_users = User.objects.filter(id__in=user_ids)
        if valid_users.count() != len(user_ids):
            raise serializers.ValidationError("Invalid user IDs included.")

        request_user = self.context["request"].user

        from accounts.utils import is_connected  

        for uid in user_ids:
            if uid == request_user.id:
                continue 

            other_user = User.objects.get(id=uid)

            if not is_connected(request_user, other_user):
                raise serializers.ValidationError(
                    f"User {uid} is not connected with you."
                )

        return user_ids

    def create(self, validated_data):
        title = validated_data.get("title", None)
        user_ids = validated_data["users"]

        conversation = Conversation.objects.create(title=title)

        for i, uid in enumerate(user_ids):
            role = "owner" if i == 0 else "member"
            ConversationUsers.objects.create(
                conversation=conversation,
                user_id=uid,
                role=role
            )

        return conversation

    def to_representation(self, instance):
        from .conversation import ConversationSerializer
        return ConversationSerializer(instance).data