#!/usr/bin/env python3
"""
Script to clear and re-index ChromaDB with URL metadata
"""

import os
import sys

# Add the rag directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import get_chroma_collection, load_urls_from_file
from index_from_url import index_urls

def clear_and_reindex():
    """Clear existing ChromaDB data and re-index with URL metadata"""
    
    print("🗑️  Clearing existing ChromaDB data...")
    try:
        collection = get_chroma_collection()
        # Get all document IDs
        all_docs = collection.get()
        if all_docs['ids']:
            collection.delete(ids=all_docs['ids'])
            print(f"✅ Cleared {len(all_docs['ids'])} existing documents")
        else:
            print("📭 No existing documents to clear")
    except Exception as e:
        print(f"⚠️ Error clearing collection: {e}")
    
    print("\n🔄 Re-indexing with URL metadata...")
    
    # Load URLs and re-index
    URLS_FILE = "diabet_urls.txt"
    urls = load_urls_from_file(URLS_FILE)
    
    if not urls:
        print(f"❌ No URLs found in {URLS_FILE}")
        return False
    
    print(f"📋 Found {len(urls)} URLs to index")
    index_urls(urls)
    
    print("\n✅ Re-indexing complete!")
    return True

if __name__ == "__main__":
    success = clear_and_reindex()
    if success:
        print("\n🎉 ChromaDB successfully updated with URL metadata!")
        print("   You can now test with: python test_chromadb.py")
    else:
        print("\n❌ Re-indexing failed!")
