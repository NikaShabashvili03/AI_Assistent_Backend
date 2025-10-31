from rest_framework import serializers
from ..models import Conversation
from chat.serializers.assistant import AssistantSerializer

class ConversationSerializer(serializers.ModelSerializer):
    assistants = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'assistants']

    def get_assistants(self, obj):
        # obj.assistants is the related_name for ConversationAssistant
        assistants_qs = [ca.assistant for ca in obj.assistants.all()]
        return AssistantSerializer(assistants_qs, many=True).data