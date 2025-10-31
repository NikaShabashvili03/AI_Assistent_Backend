from rest_framework import serializers
from ..models import Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at']

class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=5000)

    def create(self, validated_data):
            conversation = self.context.get('conversation')
            role = self.context.get('role')

            if not conversation:
                raise serializers.ValidationError("Conversation must be provided in serializer context.")
            if role not in ['user', 'assistant']:
                raise serializers.ValidationError("Role must be either 'user' or 'assistant'.")

            return Message.objects.create(
                conversation=conversation,
                role=role,
                content=validated_data['content']
            )