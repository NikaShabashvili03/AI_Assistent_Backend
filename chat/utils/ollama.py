# chat/ollama_client.py
import subprocess

OLLAMA_MODEL = "gemma3:latest"
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

        stdout, stderr = process.communicate(prompt)

        if process.returncode != 0:
            return f"Ollama error: {stderr.strip()}"

        return stdout.strip()
    except Exception as e:
        return f"Ollama exception: {e}"


# chat/ollama_client.py
# import requests
# import json

# OLLAMA_MODEL = "mistral:instruct"
# OLLAMA_URL = "http://localhost:11434"

# def ask_ollama(prompt: str) -> str:
#     try:
#         response = requests.post(
#             f"{OLLAMA_URL}/api/generate",
#             json={
#                 "model": OLLAMA_MODEL,
#                 "prompt": prompt,
#                 "stream": True
#             },
#             timeout=30,
#             stream=True
#         )
#         response.raise_for_status()

#         full_response = ""
#         for line in response.iter_lines():
#             if line:
#                 data = json.loads(line)
#                 full_response += data.get("response", "")
#                 if data.get("done", False):
#                     break
        
#         return full_response.strip()

#     except requests.exceptions.RequestException as e:
#         return f"Ollama request error: {e}"
#     except (ValueError, KeyError) as e:
#         return f"Error parsing Ollama response: {e}"