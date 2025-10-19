from django.utils import timezone
from .models import Session
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication
import threading
from .utils import get_client_ip

_user = threading.local()
_ip = threading.local()

def get_current_user():
    return getattr(_user, 'value', None)

def get_current_ip():
    return getattr(_ip, 'value', None)

class UserSessionAuthentication(BaseAuthentication):
    def authenticate(self, request):
        session_token = request.COOKIES.get('sessionId')

        if not session_token:
            _user.value = None
            _ip.value = None
            return None

        try:
            session = Session.objects.get(session_token=session_token)
        except Session.DoesNotExist:
            _user.value = None
            _ip.value = None
            raise AuthenticationFailed('Invalid session token')

        if session.expires_at > timezone.now():
            request.user = session.user
            _user.value = session.user  # Store user in thread local
            _ip.value = get_client_ip(request)  # Store IP in thread local
            return (session.user, session)
        else:
            session.delete()
            _user.value = None
            _ip.value = None
            raise AuthenticationFailed('Session expired')