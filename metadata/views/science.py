import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAuthenticated
from rest_framework import status
from ..models import Science
from ..serializers import ScienceSerializer

class ScienceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Science.objects.all()

        serializer = ScienceSerializer(conversations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
