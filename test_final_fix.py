#!/usr/bin/env python3
"""
Final test script to verify RAG system is working correctly
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_tutor.settings')
django.setup()

from knowledge_base.models import TextbookContent, ContentChunk
from protocol.faiss_driver import FAISSDriver
from context.rag_pipeline import RAGPipeline
from django.core.cache import cache

def test_database():
    """Test database state"""
    print("=== Database Test ===")
    textbooks = TextbookContent.objects.count()
    chunks = ContentChunk.objects.count()
    chunks_with_embeddings = ContentChunk.objects.filter(embedding_vector__isnull=False).count()
    
    print(f"Textbooks: {textbooks}")
    print(f"Total chunks: {chunks}")
    print(f"Chunks with embeddings: {chunks_with_embeddings}")
    
    if textbooks > 0:
        textbook = TextbookContent.objects.first()
        print(f"Sample textbook: {textbook.title} (ID: {textbook.id})")
        print(f"  Subject: {textbook.subject.name}")
        print(f"  Grade: {textbook.grade.level}")
        print(f"  Processing status: {textbook.processing_status}")
        print(f"  Chunks: {textbook.chunks.count()}")
    
    return chunks_with_embeddings > 0

def test_faiss_index():
    """Test FAISS index"""
    print("\n=== FAISS Index Test ===")
    try:
        faiss = FAISSDriver()
        index_size = faiss.index.ntotal
        print(f"FAISS index size: {index_size}")
        print(f"ID mapping keys: {len(faiss.id_mapping)}")
        print(f"Metadata keys: {len(faiss.metadata)}")
        
        if index_size > 0:
            print("✓ FAISS index has vectors")
            return True
        else:
            print("✗ FAISS index is empty")
            return False
    except Exception as e:
        print(f"✗ FAISS error: {e}")
        return False

def test_rag_pipeline():
    """Test RAG pipeline"""
    print("\n=== RAG Pipeline Test ===")
    try:
        rag = RAGPipeline()
        print("✓ RAG pipeline initialized")
        
        # Test query
        result = rag.query("What is this book about?", textbook_id='f9bdd710-6757-435e-91c9-60206c9fb726')
        print(f"✓ Query successful")
        print(f"  Context chunks: {result['context_chunks']}")
        print(f"  Response time: {result['response_time_ms']}ms")
        print(f"  Answer preview: {result['answer'][:100]}...")
        
        return result['context_chunks'] > 0
    except Exception as e:
        print(f"✗ RAG pipeline error: {e}")
        return False

def main():
    """Run all tests"""
    print("RAG System Final Test")
    print("=" * 50)
    
    # Clear cache
    cache.clear()
    print("Cache cleared")
    
    # Run tests
    db_ok = test_database()
    faiss_ok = test_faiss_index()
    rag_ok = test_rag_pipeline()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Database: {'✓ PASS' if db_ok else '✗ FAIL'}")
    print(f"FAISS Index: {'✓ PASS' if faiss_ok else '✗ FAIL'}")
    print(f"RAG Pipeline: {'✓ PASS' if rag_ok else '✗ FAIL'}")
    
    if all([db_ok, faiss_ok, rag_ok]):
        print("\n🎉 ALL TESTS PASSED! The RAG system is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 