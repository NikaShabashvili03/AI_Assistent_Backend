from rest_framework import serializers
from ..models import Assistant, AssistantTags

class AssistantTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantTags
        fields = ['id', 'name']

class AssistantSerializer(serializers.ModelSerializer):
    tag = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'  
    )

    class Meta:
        model = Assistant
        fields = ['id', 'name', 'description', 'created_at', 'tag']
