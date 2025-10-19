from rest_framework import serializers
from ..models import Assistant


class AssistantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assistant
        fields = ['id', 'name', 'created_at']
