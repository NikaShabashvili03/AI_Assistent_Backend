import tiktoken
from datetime import date
from django.utils import timezone
from accounts.models import UserTokenUsage
import os
from dotenv import load_dotenv

load_dotenv()

def count_tokens(text: str, model_name: str = os.getenv("OLLAMA_MODEL", "gemma3:latest")) -> int:
    try:
        enc = tiktoken.encoding_for_model(model_name)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def record_token_usage(user, token_count: int):
    today = timezone.now().date()
    usage, _ = UserTokenUsage.objects.get_or_create(user=user, date=today)
    usage.used_tokens += token_count
    usage.save()
    return usage

def has_tokens_left(user, token_count: int) -> bool:
    plan = user.token_plan
    if not plan:
        return False
    
    today = timezone.now().date()
    usage, _ = UserTokenUsage.objects.get_or_create(user=user, date=today)
    remaining = plan.daily_limit - usage.used_tokens
    return remaining >= token_count
