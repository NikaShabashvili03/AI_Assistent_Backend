from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAuthenticated
from rest_framework import status
from ..models import Message, Conversation, Assistant
from ..serializers import MessageSerializer, MessageCreateSerializer
from ..utils.ollama import ask_ollama

class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MessageCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        assistant_ids = request.data.get('assistant_ids', [])
        assistants = Assistant.objects.filter(id__in=assistant_ids)

        # Create user message
        user_serializer = MessageCreateSerializer(
            data=request.data,
            context={'conversation': conversation, 'role': 'user'}
        )
        user_serializer.is_valid(raise_exception=True)
        user_message = user_serializer.save()

        # Build system prompt from assistants if any
        combined_prompt = ""
        if assistants.exists():
            combined_prompt = "\n".join(
                [f"System ({a.name}): {a.prompt}" for a in assistants]
            ) + "\n"

        # Get the last 10 messages in chronological order
        previous_messages = conversation.messages.order_by('-created_at')[:10]
        previous_messages = reversed(previous_messages)  # chronological order

        conversation_history = "\n".join(f"{msg.role}: {msg.content}" for msg in previous_messages)

        # Build prompt for AI
        prompt_text = (
            "be as concise and laconic as possible, give only an answer, do not think out loud\n"
            f"{combined_prompt}"
            f"{conversation_history}\n"
            f"user: {user_message.content}"
        )

        # Call AI service
        try:
            ai_content = ask_ollama(prompt_text)
        except Exception as e:
            return Response(
                {"error": f"AI service failed: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Save assistant's response
        assistant_serializer = MessageCreateSerializer(
            data={"content": ai_content},
            context={'conversation': conversation, 'role': 'assistant'}
        )
        assistant_serializer.is_valid(raise_exception=True)
        assistant_message = assistant_serializer.save()

        first_message_from_assistant = conversation.messages.filter(role='user').first()

        conversation.title = first_message_from_assistant.content
        conversation.save()

        return Response({
            "user_message": MessageSerializer(user_message).data,
            "assistant_message": MessageSerializer(assistant_message).data,
            "assistants": [a.name for a in assistants],
            "conversation_new_title": first_message_from_assistant.content,
        }, status=status.HTTP_201_CREATED)