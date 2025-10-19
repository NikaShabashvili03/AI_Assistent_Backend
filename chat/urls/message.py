from django.urls import path
from chat.views.message import MessageListView, MessageCreateView

urlpatterns = [
    path('<int:conversation_id>/list', MessageListView.as_view(), name='list'),
    path('<int:conversation_id>/create', MessageCreateView.as_view(), name='create')
]