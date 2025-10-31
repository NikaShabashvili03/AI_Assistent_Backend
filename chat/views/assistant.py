import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAuthenticated
from rest_framework import status
from ..models import Assistant, AssistantTags
from ..serializers import AssistantSerializer, AssistantTagSerializer

class AssistantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        tags_param = request.query_params.get('tags', '')
        tags = [int(tag) for tag in tags_param.split(',') if tag.isdigit()]

        assistants = Assistant.objects.all().order_by('-created_at')
        if tags:
            assistants = assistants.filter(tag__id__in=tags).distinct()

        serializer = AssistantSerializer(assistants, many=True)
        return Response(serializer.data)

class AssistantTagListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        tags = AssistantTags.objects.all()
        serializer = AssistantTagSerializer(tags, many=True)

        return Response(serializer.data)