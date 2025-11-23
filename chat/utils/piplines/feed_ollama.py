import os
import re
import json
import uuid
import ollama
import chromadb
from mysql.connector import Error
from typing import List, Dict
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from chat.models.blog import Blog

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

class BookPipeline:
    def __init__(self):
            print("\n--- [1/3] Initializing Vector Pipeline ---")
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            

            db_path = os.path.join(script_dir, "my_book_chroma_db")
            
            print(f"ChromaDB path: {db_path}")

            self.chroma_client = chromadb.PersistentClient(path=db_path)
            self.collection = self.chroma_client.get_or_create_collection(name="book_chapters")
    
    def load_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # --- Handling PDF files ---
        if file_path.endswith('.pdf'):
            if PdfReader is None:
                raise ImportError("Install pypdf to read PDFs: pip install pypdf")
            try:
                reader = PdfReader(file_path)
                # Use 'or ""' to safely handle pages that return no text
                text = "\n".join([page.extract_text() or "" for page in reader.pages])
                return text
            except Exception as e:
                # Catch file corruption (PdfStreamError) or other read issues
                raise IOError(f"Failed to read/parse PDF file '{file_path}'. Please check file integrity. Original error: {e}")
                
        # --- Handling other files (assumed text) ---
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                raise IOError(f"Failed to read text file '{file_path}'. Check encoding or file type.")

    def split_into_chapters(self, text: str) -> List[Dict]:
        print("Splitting text into units...")
        
        pattern = r'(?i)(^Chapter\s+\d+|^Chapter\s+[A-Z][a-z]+|^\d+\.|^[IVXLCDM]+\.)'
        parts = re.split(pattern, text, flags=re.MULTILINE)
        
        units = []
        current_title = "Introduction"
        
        if len(parts) < 3:
            return self._chunk_fallback(text)

        for part in parts:
            part = part.strip()
            if not part: continue
            
            if re.match(pattern, part):
                current_title = part
            else:
                if len(part) > 500: 
                    units.append({
                        "id": str(uuid.uuid4()),
                        "title": current_title,
                        "content": part
                    })
        return units

    def _chunk_fallback(self, text, chunk_size=3000):
        units = []
        for i in range(0, len(text), chunk_size):
            units.append({
                "id": str(uuid.uuid4()),
                "title": f"Section {i//chunk_size + 1}",
                "content": text[i:i+chunk_size]
            })
        return units

    def embed_and_store(self, units: List[Dict]):
        if self.collection.count() > 0:
            print("Vectors already exist in ChromaDB. Skipping ingestion.")
            return

        print(f"Embedding {len(units)} chapters (This may take a moment)...")
        for unit in units:
            response = ollama.embeddings(model='nomic-embed-text', prompt=unit['content'])
            
            self.collection.add(
                ids=[unit['id']],
                embeddings=[response['embedding']],
                documents=[unit['content']],
                metadatas=[{"title": unit['title']}]
            )
            print(f"  > Stored: {unit['title']}")

    def generate_blog_content(self) -> List[Dict]:
        print("\n--- [2/3] Generating Blog Posts with Ollama ---")
        
        all_data = self.collection.get() 
        results = []

        if not all_data['ids']:
            print("No data found in ChromaDB.")
            return []

        total = len(all_data['ids'])
        
        for idx, doc_id in enumerate(all_data['ids']):
            text = all_data['documents'][idx]
            title = all_data['metadatas'][idx]['title']
            
            print(f"Processing ({idx+1}/{total}): {title}")
            
            prompt = f"""
                You are a book blogger. Convert this text into a structured blog post JSON.
                
                CHAPTER TITLE: {title}
                TEXT: {text[:6000]} (truncated)
                
                OUTPUT FORMAT (JSON ONLY):
                {{
                    "blog_title": "Catchy Title String",
                    "summary": "Summary string (6-10 sentences)",
                    "key_ideas": ["Point 1", "Point 2", "Point 3"]
                }}
            """
            
            try:
                response = ollama.chat(
                    model='llama3',
                    messages=[{'role': 'user', 'content': prompt}],
                    format='json' 
                )
                
                blog_json = json.loads(response['message']['content'])
                
                blog_json['original_chapter_title'] = title
                results.append(blog_json)
                
            except Exception as e:
                print(f"  [!] Error generating blog for {title}: {e}")

        return results

class DatabaseManager:
    def save_blogs(self, blog_list):
        print("\n--- [3/3] Saving to Database ---")
        if not blog_list:
            print("No blogs to save.")
            return

        try:
            for blog in blog_list:

                Blog.objects.create(
                    blog_title=blog.get('blog_title', 'Untitled'),
                    summary=blog.get('summary', ''),
                    key_ideas=blog.get('key_ideas', []), 
                    original_chapter_title=blog.get('original_chapter_title', 'Unknown')
                )
            print(f"Success! Inserted {len(blog_list)} blog posts.")
        except Exception as e:
            # Catching generic Exception for Django ORM errors
            print(f"Django ORM Insert Error: {e}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_file = os.path.join(script_dir, "digi075.pdf")
    print(f"\nAttempting to load file from: {dummy_file}\n")
    # if not os.path.exists(dummy_file):
    #      print(f"Creating dummy file at: {dummy_file}")
    #      with open(dummy_file, "w") as f:
    #          f.write("""Chapter 1: Code\nCoding is great. We use Python and Django.\nChapter 2: Data\nData must be handled carefully. It flows into MySQL.""")
    
    # with open(dummy_file, "w") as f:
    #     f.write("""
    #         Chapter 1: The Digital Horizon
    #         The server hummed with quiet energy. It was the dawn of the AI era.
    #         People everywhere were learning to code, not because they had to, but because
    #         it was the language of the future.
                    
    #         Chapter 2: The Database Connection
    #         Connecting to MySQL was the pivotal moment.
    #         Data flowed like water into the tables. The schema was perfect.
    #         Efficiency increased by 300% as the indexes aligned.
    #     """)
        
    pipeline = BookPipeline()
    
    raw_text = pipeline.load_file(dummy_file)
    chapters = pipeline.split_into_chapters(raw_text)
    
    pipeline.embed_and_store(chapters)
    
    generated_blogs = pipeline.generate_blog_content()
    
    db_manager = DatabaseManager()
    db_manager.save_blogs(generated_blogs)

    print("\nDone! Check your database.")