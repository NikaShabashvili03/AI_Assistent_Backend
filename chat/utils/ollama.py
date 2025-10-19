import subprocess

OLLAMA_MODEL = "llama3"

def ask_ollama(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL, "--prompt", prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            return f"Ollama error: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"Ollama exception: {e}"
