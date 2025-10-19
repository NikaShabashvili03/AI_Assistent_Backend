from django.urls import path, include

urlpatterns = [
    path('conversation/', include('chat.urls.conversation')),
    path('message/', include('chat.urls.message')),
    path('assistant/', include('chat.urls.assistant'))
]