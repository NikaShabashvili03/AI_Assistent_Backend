from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ..models import Conversation, ConversationUsers
from ..serializers import ConversationSerializer, ConversationCreateSerializer, ConversationUserSerializer
from ..permissions import IsConversationOwnerOrAdmin, IsConversationOwner, IsGroupConversation

from accounts.models import User
from accounts.utils import is_connected

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100

class ConversationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        
        conversations = Conversation.objects.filter(
            conversation_users__user=request.user
        ).distinct()

        if search:
            conversations = conversations.filter(
                Q(title__icontains=search) |
                Q(conversation_users__user__firstname__icontains=search)
            ).distinct()

        conversations = conversations.order_by("-created_at")
        
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(conversations, request)
        serializer = ConversationSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        conversation = get_object_or_404(Conversation, id=id, conversation_users__user=request.user)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

class ConversationCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ConversationCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ConversationDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsConversationOwner]

    def delete(self, request, id):
        conversation = get_object_or_404(Conversation, id=id)
        self.check_object_permissions(request, conversation)
        conversation.delete()
        return Response({"success": True, "id": id}, status=status.HTTP_200_OK)

class AddUsersToConversationView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsConversationOwnerOrAdmin, IsGroupConversation]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        self.check_object_permissions(request, conversation)

        user_ids = request.data.get("user_ids", [])
        if not isinstance(user_ids, list) or not user_ids:
            return Response({"error": "user_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

        added_users = []
        invalid_users = []

        existing_member_ids = set(conversation.conversation_users.values_list('user_id', flat=True))

        for uid in user_ids:
            if uid in existing_member_ids:
                continue

            try:
                user = User.objects.get(id=uid)
                if is_connected(request.user, user):
                    ConversationUsers.objects.create(conversation=conversation, user=user, role="member")
                    added_users.append(uid)
                else:
                    invalid_users.append(uid)
            except User.DoesNotExist:
                invalid_users.append(uid)

        return Response({
            "success": True,
            "added_count": len(added_users),
            "added_users": added_users,
            "invalid_users": invalid_users
        })

class LeaveConversationView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsGroupConversation]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        self.check_object_permissions(request, conversation)
        
        cu = get_object_or_404(ConversationUsers, conversation=conversation, user=request.user)

        if cu.role == "owner":
            owner_count = ConversationUsers.objects.filter(conversation=conversation, role="owner").count()
            if owner_count == 1:
                return Response(
                    {"error": "You are the only owner. Transfer ownership before leaving or delete the conversation."}, 
                    status=status.HTTP_403_FORBIDDEN
                )

        cu.delete()
        
        if conversation.conversation_users.count() == 0:
            conversation.delete()

        return Response({"success": True, "message": "You have left the conversation."})

class TransferOwnershipSwapView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsConversationOwner, IsGroupConversation]

    def post(self, request, conversation_id, user_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        self.check_object_permissions(request, conversation)

        current_owner = get_object_or_404(ConversationUsers, conversation=conversation, user=request.user)
        target_user = get_object_or_404(ConversationUsers, conversation=conversation, user_id=user_id)

        if current_owner.user_id == target_user.user_id:
            return Response({"error": "Cannot transfer ownership to yourself"}, status=status.HTTP_400_BAD_REQUEST)

        previous_target_role = target_user.role
        target_user.role = "owner"
        current_owner.role = previous_target_role 

        target_user.save()
        current_owner.save()

        return Response({
            "success": True,
            "message": f"Ownership transferred to {target_user.user.firstname}."
        })

class RemoveUserFromConversationView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsConversationOwnerOrAdmin, IsGroupConversation]

    def post(self, request, conversation_id, user_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        self.check_object_permissions(request, conversation)

        target_cu = get_object_or_404(ConversationUsers, conversation=conversation, user_id=user_id)

        if target_cu.role == "owner":
            return Response({"error": "Cannot remove an owner."}, status=status.HTTP_403_FORBIDDEN)

        target_cu.delete()
        return Response({"success": True, "message": "User removed."})

class ConversationUserList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if not ConversationUsers.objects.filter(conversation=conversation, user=request.user).exists():
             return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        members = ConversationUsers.objects.filter(conversation=conversation).select_related('user')
        return Response(ConversationUserSerializer(members, many=True).data)