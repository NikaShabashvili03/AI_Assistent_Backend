from django.urls import path, include

urlpatterns = [
    path('science/', include('metadata.urls.science')),
]