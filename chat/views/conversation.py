from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from ..models import Conversation, ConversationUsers
from ..serializers import ConversationSerializer, MessageCreateSerializer, ConversationCreateSerializer
from accounts.permissions import IsAuthenticated
from ..utils.ollama import ask_ollama
from accounts.utils import is_connected

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
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        try:
            conversation = Conversation.objects.get(
                id=id, conversation_users__user=request.user
            )
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        conversation.delete()
        return Response({"id": id}, status=status.HTTP_200_OK)
