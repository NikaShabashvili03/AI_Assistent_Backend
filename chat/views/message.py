from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAuthenticated
from rest_framework import status
from ..models import Message, Conversation
from ..serializers import MessageSerializer, MessageCreateSerializer
from ..utils.ollama import ask_ollama
from ..utils.tokens import count_tokens, record_token_usage, has_tokens_left
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                conversation_users__user=request.user
            )
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MessageCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                conversation_users__user=request.user
            )
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        user_serializer = MessageCreateSerializer(
            data=request.data,
            context={'conversation': conversation, 'role': 'user', 'user': request.user}
        )
        user_serializer.is_valid(raise_exception=True)
        user_message = user_serializer.save()

        self.send_ws_message(conversation_id, user_message)

        content_lower = user_message.content.lower()

        if "@geobot" not in content_lower and conversation.conversation_users.count() == 2:
            return Response({
                "user_message": MessageSerializer(user_message).data,
                "assistant_message": None,
                "tokens": None
            }, status=status.HTTP_201_CREATED)

        previous_messages = conversation.messages.order_by('-created_at')[:10]
        previous_messages = reversed(previous_messages)
        conversation_history = "\n".join(
            f"{msg.role}: {msg.content}" for msg in previous_messages
        )

        prompt_text = (
            "be as concise and laconic as possible, give only an answer, do not think out loud\n"
            f"{conversation_history}\n"
            f"user: {user_message.content}"
        )

        input_tokens = count_tokens(prompt_text)
        if not has_tokens_left(request.user, input_tokens):
            return Response(
                {"error": "Daily token limit reached."},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        try:
            ai_content = ask_ollama(prompt_text)
        except Exception as e:
            return Response({"error": f"AI service failed: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        output_tokens = count_tokens(ai_content)
        total_tokens = input_tokens + output_tokens
        record_token_usage(request.user, total_tokens)

        assistant_serializer = MessageCreateSerializer(
            data={"content": ai_content},
            context={'conversation': conversation, 'role': 'assistant'}
        )
        assistant_serializer.is_valid(raise_exception=True)
        assistant_message = assistant_serializer.save()

        self.send_ws_message(conversation_id, assistant_message)

        return Response({
            "user_message": MessageSerializer(user_message).data,
            "assistant_message": MessageSerializer(assistant_message).data,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens
            }
        }, status=status.HTTP_201_CREATED)

    def send_ws_message(self, conversation_id, message_obj):
        channel_layer = get_channel_layer()
        group_name = f"chat_{conversation_id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "chat_message",
                "message": message_obj.content,
                "role": message_obj.role,
                "sender": message_obj.sent_by.id if message_obj.sent_by else None,
                "created_at": message_obj.created_at.isoformat()
            }
        )
