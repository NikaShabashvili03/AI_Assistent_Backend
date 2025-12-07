from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('accounts.urls')),
    path('api/v2/', include('chat.urls')),
    path('api/v3/', include('metadata.urls')),
    path("api/subscriptions/", include("subscriptions.urls")),
]
