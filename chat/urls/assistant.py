from django.urls import path
from chat.views.assistant import AssistantListView, AssistantTagListView

urlpatterns = [
    path('list', AssistantListView.as_view(), name='list'),
    path('tag/list', AssistantTagListView.as_view(), name='tag-list')
]