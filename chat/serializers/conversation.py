from rest_framework import serializers
from django.db.models import Q
from ..models import Conversation, ConversationUsers
from accounts.serializers import UserSerializer
from accounts.models import User
from accounts.utils import is_connected

class ConversationUserSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = ConversationUsers
        fields = ["user", "joined_at", "role"]

class ConversationSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ["id", "title", "is_group", "created_at", "users"]

    def get_users(self, obj):
        users = obj.conversation_users.select_related('user').all()
        return ConversationUserSerializer(users, many=True).data

class ConversationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    users = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        write_only=True
    )

    def validate_users(self, user_ids):
        user_ids = list(set(user_ids))
        request_user = self.context["request"].user

        if request_user.id in user_ids:
            user_ids.remove(request_user.id)

        if not user_ids:
            raise serializers.ValidationError("You must include at least one other user.")

        valid_users = User.objects.filter(id__in=user_ids)
        if valid_users.count() != len(user_ids):
            raise serializers.ValidationError("One or more user IDs are invalid.")

        for target_user in valid_users:
            if not is_connected(request_user, target_user):
                 raise serializers.ValidationError(f"User {target_user.id} is not connected with you.")

        return user_ids

    def create(self, validated_data):
        title = validated_data.get("title", None)
        user_ids = validated_data["users"]
        request_user = self.context["request"].user
        
        all_participant_ids = [request_user.id] + user_ids
        is_group = len(all_participant_ids) > 2

        if not is_group:
            other_user_id = user_ids[0]
            existing = Conversation.objects.filter(
                is_group=False,
                conversation_users__user_id=request_user.id
            ).filter(
                conversation_users__user_id=other_user_id
            ).first()

            if existing:
                return existing

        conversation = Conversation.objects.create(
            title=title if is_group else None,
            is_group=is_group
        )

        conversation_users = []
        for uid in all_participant_ids:
            if not is_group:
                role = "owner"
            else:
                role = "owner" if uid == request_user.id else "member"
            
            conversation_users.append(
                ConversationUsers(conversation=conversation, user_id=uid, role=role)
            )

        ConversationUsers.objects.bulk_create(conversation_users)

        return conversation
    
    def to_representation(self, instance):
        return ConversationSerializer(instance).data