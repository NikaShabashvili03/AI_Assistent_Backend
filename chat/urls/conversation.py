from django.urls import path
from chat.views.conversation import ConversationListView, ConversationDetailView, ConversationCreateView, ConversationDeleteView, LeaveConversationView, TransferOwnershipSwapView, AddUsersToConversationView, RemoveUserFromConversationView

urlpatterns = [
    path('list', ConversationListView.as_view(), name='list'),
    path('details/<int:id>', ConversationDetailView.as_view(), name='details'),
    path('create', ConversationCreateView.as_view(), name='create'),
    path('delete/<int:id>', ConversationDeleteView.as_view(), name='delete'),
    path("leave/<int:conversation_id>", LeaveConversationView.as_view(), name="conversation-leave"),
    path("transfer/<int:conversation_id>/<int:user_id>", TransferOwnershipSwapView.as_view(), name="conversation-transfer-ownership"),
    path("users/add/<int:conversation_id>", AddUsersToConversationView.as_view(),name="conversation-add-users"),
    path("user/remove/<int:conversation_id>/<int:user_id>",RemoveUserFromConversationView.as_view(),name="conversation-remove-user"),
]