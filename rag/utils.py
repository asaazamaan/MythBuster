import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import chromadb

def fetch_and_chunk(url, chunk_size=300):
    res = requests.get(url, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")
    paragraphs = [p.get_text() for p in soup.find_all("p") if p.get_text(strip=True)]
    text = "\n".join(paragraphs)
    
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def get_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

def get_chroma_collection():
    client = chromadb.PersistentClient(path="../.chromadb")
    return client.get_or_create_collection("medical_facts")

def load_urls_from_file(file_path):
    """Load URLs from a text file, one URL per line."""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                url = line.strip()
                if url and not url.startswith('#'):  # Skip empty lines and comments
                    urls.append(url)
        return urls
    except FileNotFoundError:
        print(f"❌ URL file not found: {file_path}")
        return []
    except Exception as e:
        print(f"❌ Error reading URL file: {e}")
        return []
