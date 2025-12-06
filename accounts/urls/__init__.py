from django.urls import path, include

urlpatterns = [
    path('user/', include('accounts.urls.user')),
    path('log/', include('accounts.urls.log')),
    path('connection/', include('accounts.urls.connection')),
]