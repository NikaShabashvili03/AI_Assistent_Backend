from rest_framework import generics, status
from rest_framework.response import Response
from ..permissions import AllowAny, IsAuthenticated
from ..serializers import UserSerializer, UserLoginSerializer, UserRegisterViewSerializer
from django.middleware.csrf import get_token
import uuid
from django.utils.timezone import now
from datetime import timedelta
from ..models import Session
from ..utils import get_client_ip
from rest_framework.views import APIView
from accounts.models import User
    
class RegisterView(generics.GenericAPIView):
    serializer_class = UserRegisterViewSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        user_data = UserSerializer(user).data
        return Response(user_data, status=status.HTTP_200_OK)
    
class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):  
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        csrf_token = get_token(request)

        user = serializer.validated_data

        token = str(uuid.uuid4())
        user.last_login = now()
        user.save()

        expires_at = now() + timedelta(days=2)

        session = Session.objects.create(
            user=user,
            session_token=token,
            ip=get_client_ip(request),
            expires_at=expires_at,
        )

        user_data = UserSerializer(user).data

        response = Response(user_data, status=status.HTTP_200_OK)
        response.set_cookie(
            'sessionId', session.session_token, expires=expires_at, 
            samesite='None', secure=True
        )
        csrf_token = get_token(request)
        response['X-CSRFToken'] = csrf_token
        return response
    
class ProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, context={'request': request})

        return Response(serializer.data)

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        sessions = Session.objects.filter(user_id=user).distinct()
        response = Response({'details': 'Logged out successfully'}, status=status.HTTP_200_OK)
        if sessions:
            sessions.delete()
            response.delete_cookie('sessionId')
        else:
            response = Response({'details': 'Invalid session token'}, status=status.HTTP_400_BAD_REQUEST)
            
        return response