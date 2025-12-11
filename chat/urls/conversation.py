from django.urls import path
from ..views.conversation import (
    ConversationListView, ConversationDetailView, ConversationCreateView,
    ConversationDeleteView, LeaveConversationView, TransferOwnershipSwapView,
    AddUsersToConversationView, RemoveUserFromConversationView, ConversationUserList,
    RenameConversationView
)

urlpatterns = [
    path('list', ConversationListView.as_view(), name='conversation-list'),
    path('create', ConversationCreateView.as_view(), name='conversation-create'),
    path('details/<int:id>', ConversationDetailView.as_view(), name='conversation-detail'),
    path('delete/<int:id>', ConversationDeleteView.as_view(), name='conversation-delete'),
    
    path('leave/<int:conversation_id>', LeaveConversationView.as_view(), name='conversation-leave'),
    path('transfer/<int:conversation_id>/<int:user_id>', TransferOwnershipSwapView.as_view(), name='conversation-transfer'),
    path('users/add/<int:conversation_id>', AddUsersToConversationView.as_view(), name='conversation-add-users'),
    path('users/remove/<int:conversation_id>/<int:user_id>', RemoveUserFromConversationView.as_view(), name='conversation-remove-user'),
    path('users/list/<int:conversation_id>', ConversationUserList.as_view(), name='conversation-user-list'),

    path("rename/<int:conversation_id>", RenameConversationView.as_view()),
]