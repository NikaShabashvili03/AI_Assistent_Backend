from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAuthenticated
from rest_framework import status
from ..models import Message, Conversation, Assistant
from ..serializers import MessageSerializer, MessageCreateSerializer
import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1"

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
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        assistant_ids = request.data.get('assistant_ids', [])
        assistants = Assistant.objects.filter(id__in=assistant_ids)

        user_serializer = MessageCreateSerializer(
            data=request.data,
            context={'conversation': conversation, 'role': 'user'}
        )
        user_serializer.is_valid(raise_exception=True)
        user_message = user_serializer.save()

        combined_prompt = ""
        if assistants.exists():
            combined_prompt = "\n".join(
                [f"System ({a.name}): {a.prompt}" for a in assistants]
            ) + "\n"

        previous_messages = conversation.messages.order_by('created_at')
        conversation_history = "\n".join(f"{msg.role}: {msg.content}" for msg in previous_messages)
        prompt_text = f"{combined_prompt}{conversation_history}\nuser: {user_message.content}"

        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={"model": MODEL_NAME, "prompt": prompt_text},
                timeout=60
            )
            response.raise_for_status()

            ai_responses = []
            for line in response.text.strip().split("\n"):
                try:
                    obj = json.loads(line)
                    if "response" in obj:
                        ai_responses.append(obj["response"])
                except json.JSONDecodeError:
                    continue

            ai_content = "".join(ai_responses) if ai_responses else "No response from AI."
        except Exception as e:
            ai_content = f"Ollama error: {e}"

        assistant_serializer = MessageCreateSerializer(
            data={"content": ai_content},
            context={'conversation': conversation, 'role': 'assistant'}
        )
        assistant_serializer.is_valid(raise_exception=True)
        assistant_message = assistant_serializer.save()

        return Response({
            "user_message": MessageSerializer(user_message).data,
            "assistant_message": MessageSerializer(assistant_message).data,
            "assistants": [a.name for a in assistants],
        }, status=status.HTTP_201_CREATED)