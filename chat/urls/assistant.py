from django.urls import path
from chat.views.assistant import AssistantListView

urlpatterns = [
    path('list', AssistantListView.as_view(), name='list'),
]