# chat/ollama_client.py
# import subprocess
# import os
# from dotenv import load_dotenv


# load_dotenv()

# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:latest")
# OLLAMA_PATH = os.getenv("OLLAMA_PATH", "/snap/bin/ollama")

# def ask_ollama(prompt: str) -> str:
#     try:
#         process = subprocess.Popen(
#             [OLLAMA_PATH, "run", OLLAMA_MODEL],
#             stdin=subprocess.PIPE,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True
#         )

#         stdout, stderr = process.communicate(prompt)

#         if process.returncode != 0:
#             return f"Ollama error: {stderr.strip()}"

#         return stdout.strip()
#     except Exception as e:
#         return f"Ollama exception: {e}"

import requests
import json
import chromadb
from typing import List, Dict

OLLAMA_URL = "http://localhost:11434"
GEN_MODEL = "mistral:instruct"           
EMBED_MODEL = "nomic-embed-text" 

def ask_ollama(prompt: str, json_format: bool = False) -> str:
    payload = {
        "model": GEN_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {"num_predict": 1024} 
    }
    if json_format:
        payload["format"] = "json"

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=120,
            stream=True
        )
        response.raise_for_status()

        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    full_response += data.get("response", "")
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    print(f"DEBUG: Could not decode JSON line: {line.decode('utf-8')[:50]}...")

        return full_response.strip()

    except requests.exceptions.RequestException as e:
        print(f"Error: Ollama request error. Is Ollama running? {e}")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return ""

class OllamaEmbeddingFunction(chromadb.EmbeddingFunction):
    def __call__(self, texts: List[str]) -> List[List[float]]:
        print(f"DEBUG: Generating {len(texts)} embeddings with {EMBED_MODEL}...")
        embeddings = []
        for text in texts:
            try:
                
                response = requests.post(
                    f"{OLLAMA_URL}/api/embeddings",
                    json={
                        "model": EMBED_MODEL,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["embedding"])
            except Exception as e:
                print(f"Error embedding text: {text[:30]}... Error: {e}")
                
                embeddings.append([]) 
        return embeddings


def run_rag_pipeline(question: str):
    DB_PATH = "./piplines/my_book_chroma_db"
    
    embed_fn = OllamaEmbeddingFunction()
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    collection = chroma_client.get_or_create_collection(
        name="knowledge_base",
        embedding_function=embed_fn
    )

    if collection.count() == 0:
        collection.add(
            documents=["Ollama runs LLMs locally.", "ChromaDB stores vectors.", "RAG connects an LLM to data."],
            ids=["doc1", "doc2", "doc3"]
        )
        print("Indexed initial data.")

    # 1. Retrieve Context
    results = collection.query(
        query_texts=[question],
        n_results=2
    )
    
    retrieved_context = "\n".join(results['documents'][0])

    # 2. Augment Prompt and Generate Answer
    prompt = f"""
    Use the following CONTEXT to answer the QUESTION. If the context is irrelevant, state that you cannot answer from the given information.

    CONTEXT:
    {retrieved_context}

    QUESTION: {question}

    ANSWER:
    """
    
    answer = ask_ollama(prompt)
    print("\n--- Final Answer ---")
    print(answer)
    print("--------------------\n")
    return answer

if __name__ == "__main__":
    # Ensure Ollama is running and both models (llama3, nomic-embed-text) are pulled!
    # To run: python ollama_client.py
    run_rag_pipeline("What is RAG used for and how does ChromaDB fit in?")