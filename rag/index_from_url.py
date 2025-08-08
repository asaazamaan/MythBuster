from utils import fetch_and_chunk, get_embedder, get_chroma_collection, load_urls_from_file
from uuid import uuid4

# Load URLs from the text file
URLS_FILE = "diabet_urls.txt"
URLS = load_urls_from_file(URLS_FILE)

def index_urls(urls):
    embedder = get_embedder()
    collection = get_chroma_collection()
    
    for url in urls:
        try:
            print(f"🔗 Fetching: {url}")
            chunks = fetch_and_chunk(url)
            embeddings = embedder.encode(chunks).tolist()
            ids = [str(uuid4()) for _ in chunks]
            
            # Create metadata for each chunk with the source URL
            metadatas = [{"source_url": url} for _ in chunks]
            
            collection.add(
                documents=chunks, 
                embeddings=embeddings, 
                ids=ids,
                metadatas=metadatas
            )
            print(f"✅ Indexed {len(chunks)} chunks from {url}")
        except Exception as e:
            print(f"❌ Failed on {url}: {e}")

if __name__ == "__main__":
    if not URLS:
        print(f"❌ No URLs found in {URLS_FILE}")
        exit(1)
    
    print(f"📋 Loaded {len(URLS)} URLs from {URLS_FILE}")
    index_urls(URLS)
