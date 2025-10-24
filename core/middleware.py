from channels.middleware import BaseMiddleware
from rest_framework.exceptions import AuthenticationFailed
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from channels.db import database_sync_to_async

class CustomWebSocketMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner
        super().__init__(inner) 

    async def __call__(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        cookies = headers.get(b'cookie', b'').decode('utf-8')
        print("RAW COOKIES HEADER:", cookies)


        session_token = self.get_cookie_value(cookies, 'sessionId')
        scope['session_token'] = session_token
        
        if session_token:
            from django.apps import apps
            from accounts.models import Session

            apps.get_app_config('accounts') 

            try:
                session = await database_sync_to_async(Session.objects.get)(session_token=session_token)
                user = await database_sync_to_async(lambda: session.user)()

                if session.expires_at > timezone.now():
                    scope['user'] = user 
                    # await self.set_online(user)
                else:
                    await database_sync_to_async(session.delete)() 
                    await self.close_connection(send, code=4003, message="Session expired")
                    return
            except Session.DoesNotExist:
                await self.close_connection(send, code=4003, message="Invalid session token")
                return
        else:
            return await self.close_connection(send, code=4003, message="Invalid session token")
        
        return await self.inner(scope, receive, send)
    
    @staticmethod
    async def close_connection(send, code, message):
        await send({
            "type": "websocket.close", 
            "code": code,
            "reason": message,
        })

    @staticmethod
    def get_cookie_value(cookie_header, key):
        cookies = {}
        for cookie in cookie_header.split(';'):
            name, _, value = cookie.strip().partition('=')
            cookies[name.lower()] = value
        return cookies.get(key.lower())
    
    # @staticmethod
    # @database_sync_to_async
    # def set_online(user):
    #     from accounts.models import OnlineStatus
    #     obj, _ = OnlineStatus.objects.get_or_create(user=user)
    #     obj.is_online = True
    #     obj.last_seen = timezone.now()
    #     obj.save()

    # @staticmethod
    # @database_sync_to_async
    # def set_offline(user):
    #     from accounts.models import OnlineStatus
    #     obj, _ = OnlineStatus.objects.get_or_create(user=user)
    #     obj.is_online = False
    #     obj.last_seen = timezone.now()
    #     obj.save()