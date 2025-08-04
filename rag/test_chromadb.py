#!/usr/bin/env python3
"""
Simple test script to verify ChromaDB is working with indexed diabetes data
"""

from utils import get_chroma_collection, get_embedder

def test_chromadb():
    print("🔬 Testing ChromaDB with diabetes knowledge base...")
    print("=" * 50)
    
    try:
        # Get the collection
        collection = get_chroma_collection()
        
        # Check if we have data
        count = collection.count()
        print(f"📊 Total documents in collection: {count}")
        
        if count == 0:
            print("❌ No documents found! ChromaDB appears to be empty.")
            return False
        
        # Test 1: Basic retrieval
        print("\n📋 Test 1: Retrieving all documents...")
        all_docs = collection.get()
        print(f"✅ Successfully retrieved {len(all_docs['documents'])} documents")
        
        # Show first document sample
        if all_docs['documents']:
            first_doc = all_docs['documents'][0]
            print(f"📄 First document preview: {first_doc[:100]}...")
        
        # Test 2: Similarity search
        print("\n🔍 Test 2: Testing similarity search...")
        test_queries = [
            "What are the symptoms of diabetes?",
            "How is type 2 diabetes treated?",
            "What causes diabetes?"
        ]
        
        for query in test_queries:
            print(f"\n❓ Query: '{query}'")
            results = collection.query(
                query_texts=[query],
                n_results=2
            )
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 'N/A'
                    print(f"   📄 Result {i+1} (distance: {distance:.3f}): {doc[:80]}...")
            else:
                print("   ⚠️ No results found")
        
        # Test 3: Embedder functionality
        print("\n🧠 Test 3: Testing embedder...")
        embedder = get_embedder()
        test_text = "diabetes symptoms include frequent urination"
        embedding = embedder.encode([test_text])
        print(f"✅ Generated embedding with shape: {embedding.shape}")
        
        print("\n🎉 All tests completed successfully!")
        print(f"✅ ChromaDB is working with {count} diabetes-related documents")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chromadb()
    if success:
        print("\n🚀 Ready to use for fact-checking!")
    else:
        print("\n🔧 Please check the ChromaDB setup")
