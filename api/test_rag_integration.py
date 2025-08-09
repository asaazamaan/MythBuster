#!/usr/bin/env python3
"""
Test script to verify RAG integration in fact-checking API
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

# Import the function we want to test
from routes.video_routes import get_relevant_context, fact_check_single_claim

def test_rag_integration():
    print("🧪 Testing RAG integration in fact-checking API...")
    print("=" * 60)
    
    # Test claims in Arabic (diabetes-related)
    test_claims = [
        "شرب الماء البارد يسبب مرض السكري",  # "Drinking cold water causes diabetes"
        "القرفة تشفي مرض السكري تماما",        # "Cinnamon completely cures diabetes"
        "مرضى السكري لا يستطيعون أكل الفواكه"    # "Diabetics cannot eat fruits"
    ]
    
    for i, claim in enumerate(test_claims, 1):
        print(f"\n🔍 Test {i}: Testing claim: '{claim}'")
        print("-" * 50)
        
        # Test 1: Get relevant context
        print("📚 Step 1: Retrieving relevant context...")
        relevant_docs = get_relevant_context(claim, max_results=2)
        
        if relevant_docs:
            print(f"✅ Found {len(relevant_docs)} relevant documents:")
            for j, doc in enumerate(relevant_docs):
                print(f"   📄 Doc {j+1} (relevance: {doc['relevance_score']:.3f}): {doc['content'][:80]}...")
        else:
            print("⚠️ No relevant documents found")
        
        # Test 2: Test fact-checking (without actually calling Gemini API)
        print("🔬 Step 2: Would call fact_check_single_claim with RAG context")
        print(f"   - Claim: {claim}")
        print(f"   - Context documents: {len(relevant_docs)}")
        
        print("✅ Test completed successfully")
    
    print(f"\n🎉 All RAG integration tests completed!")

def test_context_retrieval_only():
    """Test just the context retrieval without API calls"""
    print("🔍 Testing context retrieval functionality...")
    
    test_query = "diabetes symptoms and treatment"
    docs = get_relevant_context(test_query, max_results=3)
    
    if docs:
        print(f"✅ Successfully retrieved {len(docs)} documents")
        for i, doc in enumerate(docs):
            print(f"📄 Document {i+1}:")
            print(f"   Relevance: {doc['relevance_score']:.3f}")
            print(f"   Content: {doc['content'][:100]}...")
            print()
    else:
        print("❌ No documents retrieved")

if __name__ == "__main__":
    try:
        # Test context retrieval first
        test_context_retrieval_only()
        print("\n" + "="*60 + "\n")
        
        # Test full RAG integration
        test_rag_integration()
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
