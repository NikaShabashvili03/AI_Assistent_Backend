from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Log
from ..serializers import LogSerializer

class LogListView(APIView):
    def get(self, request):
        queryset = Log.objects.all().order_by('-timestamp')

        model_name = request.query_params.get('model_name')
        action = request.query_params.get('action')

        if model_name:
            queryset = queryset.filter(model_name__iexact=model_name)
        if action:
            queryset = queryset.filter(action__iexact=action)

        serializer = LogSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
