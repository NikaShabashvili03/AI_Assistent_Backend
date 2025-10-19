import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAuthenticated
from rest_framework import status
from ..models import Assistant
from ..serializers import AssistantSerializer

class AssistantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Assistant.objects.all().order_by('-created_at')
        serializer = AssistantSerializer(conversations, many=True)
        return Response(serializer.data)
