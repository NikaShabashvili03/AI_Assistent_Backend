from ..serializers import MessageSerializer, MessageCreateSerializer
from ..models import Message, Conversation, Assistant
import subprocess

OLLAMA_MODEL = "llama3"
OLLAMA_PATH = "/snap/bin/ollama"

def ask_ollama(prompt: str) -> str:
    try:
        process = subprocess.Popen(
            [OLLAMA_PATH, "run", OLLAMA_MODEL],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(prompt + "\n")  # add newline
        if process.returncode != 0:
            return f"Ollama error: {stderr.strip()}"
        return stdout.strip()
    except Exception as e:
        return f"Ollama exception: {e}"
