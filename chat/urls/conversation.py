from django.urls import path
from chat.views.conversation import ConversationListView, ConversationDetailView, ConversationCreateView

urlpatterns = [
    path('list', ConversationListView.as_view(), name='list'),
    path('details/<int:id>', ConversationDetailView.as_view(), name='details'),
    path('create', ConversationCreateView.as_view(), name='create')
]