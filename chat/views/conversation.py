from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from ..models import Conversation, ConversationUsers
from ..serializers import ConversationSerializer, ConversationCreateSerializer
from accounts.permissions import IsAuthenticated
from ..utils.ollama import ask_ollama
from accounts.utils import is_connected
from ..permissions import IsConversationOwnerOrAdmin, IsConversationOwner
from accounts.models import User

class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = request.query_params.get("limit")
        search = request.query_params.get("search", "").strip()

        conversations = Conversation.objects.filter(
            conversation_users__user=request.user
        ).distinct()

        if search:
            conversations = conversations.filter(
                Q(title__icontains=search) |
                Q(messages__content__icontains=search) |
                Q(conversation_users__user__firstname__icontains=search)
            ).distinct()

        conversations = conversations.order_by("-created_at")

        if limit:
            try:
                limit = int(limit)
                conversations = conversations[:limit]
            except ValueError:
                return Response({"error": "Invalid limit value"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            conversation = Conversation.objects.get(
                id=id, conversation_users__user=request.user
            )
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)


class ConversationCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationCreateSerializer

    def post(self, request):
        data = request.data.copy()

        creator_id = request.user.id
        users = data.get("users", [])

        if not isinstance(users, list):
            users = [users]

        users = list(set(users))

        if creator_id in users:
            users.remove(creator_id)
        users.insert(0, creator_id)

        data["users"] = users

        create_serializer = self.serializer_class(
            data=data,
            context={"request": request}
        )
        create_serializer.is_valid(raise_exception=True)
        conversation = create_serializer.save()

        response_serializer = ConversationSerializer(conversation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class ConversationDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsConversationOwner]

    def delete(self, request, id):
        try:
            conversation = Conversation.objects.get(id=id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=404)

        self.check_object_permissions(request, conversation)
        conversation.delete()
        return Response({"id": id}, status=200)
    
class AddUsersToConversationView(APIView):
    permission_classes = [IsAuthenticated, IsConversationOwnerOrAdmin]

    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=404)

        self.check_object_permissions(request, conversation)

        user_ids = request.data.get("user_ids", [])

        if not user_ids or not isinstance(user_ids, list):
            return Response({"error": "user_ids must be a non-empty list"}, status=400)

        added_users = []
        invalid_users = []

        for uid in user_ids:
            try:
                user = User.objects.get(id=uid)
            except User.DoesNotExist:
                invalid_users.append(uid)
                continue

            if not is_connected(request.user, user):
                invalid_users.append(uid)
                continue

            obj, created = ConversationUsers.objects.get_or_create(
                conversation=conversation,
                user=user,
                defaults={"role": "member"}
            )
            if created:
                added_users.append(uid)

        return Response({
            "success": True,
            "added_users": added_users,
            "invalid_users": invalid_users,
            "message": f"{len(added_users)} user(s) added, {len(invalid_users)} invalid or not connected"
        }, status=200)
    
class LeaveConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            cu = ConversationUsers.objects.get(conversation=conversation, user=request.user)
        except (Conversation.DoesNotExist, ConversationUsers.DoesNotExist):
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        if cu.role == "owner":
            return Response({"error": "Owner cannot leave the conversation. Delete it instead."},
                            status=status.HTTP_403_FORBIDDEN)

        cu.delete()
        return Response({"success": True, "message": "You have left the conversation."}, status=status.HTTP_200_OK)
    
class DeleteConversationView(APIView):
    permission_classes = [IsAuthenticated, IsConversationOwner]

    def delete(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, conversation)
        conversation.delete()
        return Response({"success": True, "message": "Conversation deleted."}, status=status.HTTP_200_OK)
    
class TransferOwnershipSwapView(APIView):
    permission_classes = [IsAuthenticated, IsConversationOwner]

    def post(self, request, conversation_id, user_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, conversation)

        try:
            current_owner = ConversationUsers.objects.get(conversation=conversation, user=request.user)
        except ConversationUsers.DoesNotExist:
            return Response({"error": "You are not part of this conversation"}, status=status.HTTP_403_FORBIDDEN)

        try:
            target_user = ConversationUsers.objects.get(conversation=conversation, user_id=user_id)
        except ConversationUsers.DoesNotExist:
            return Response({"error": "Target user is not in this conversation"}, status=status.HTTP_404_NOT_FOUND)

        if current_owner.user_id == target_user.user_id:
            return Response({"error": "Cannot transfer ownership to yourself"}, status=status.HTTP_400_BAD_REQUEST)

        current_owner.role, target_user.role = target_user.role, current_owner.role
        target_user.role = "owner" 
        current_owner.save()
        target_user.save()

        return Response({
            "success": True,
            "message": f"Ownership transferred to {target_user.user.firstname} with role swap."
        }, status=status.HTTP_200_OK)
    

class RemoveUserFromConversationView(APIView):
    permission_classes = [IsAuthenticated, IsConversationOwnerOrAdmin]

    def post(self, request, conversation_id, user_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, conversation)

        try:
            target_user = ConversationUsers.objects.get(conversation=conversation, user_id=user_id)
        except ConversationUsers.DoesNotExist:
            return Response({"error": "User not in this conversation"}, status=status.HTTP_404_NOT_FOUND)

        if target_user.role == "owner":
            return Response({"error": "Cannot remove the owner from the conversation"}, status=status.HTTP_403_FORBIDDEN)

        target_user.delete()

        return Response({
            "success": True,
            "message": f"{target_user.user.firstname} has been removed from the conversation."
        }, status=status.HTTP_200_OK)