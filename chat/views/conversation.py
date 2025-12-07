from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from ..models import Conversation, ConversationUsers
from ..serializers import ConversationSerializer, MessageCreateSerializer
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

    def post(self, request):
        conversation = Conversation.objects.create(
            title=request.data.get("title", "New Conversation")
        )

        ConversationUsers.objects.create(conversation=conversation, user=request.user)

        message_content = request.data.get("content", "Hello!")

        user_serializer = MessageCreateSerializer(
            data={"content": message_content},
            context={'conversation': conversation, 'role': 'user'}
        )
        
        user_serializer.is_valid(raise_exception=True)
        user_message = user_serializer.save()

        prompt_text = (
            "be as concise and laconic as possible, give only an answer, do not think out loud\n"
            f"user: {user_message.content}"
        )
        try:
            ai_content = ask_ollama(prompt_text)
        except Exception as e:
            return Response(
                {"error": f"AI service failed: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        message_serializer = MessageCreateSerializer(
            data={"content": ai_content},
            context={'conversation': conversation, 'role': 'assistant'}
        )
        message_serializer.is_valid(raise_exception=True)
        message_serializer.save()

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
