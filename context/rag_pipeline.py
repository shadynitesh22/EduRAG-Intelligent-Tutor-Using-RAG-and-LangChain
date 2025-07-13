from typing import List, Dict, Any, Optional
from django.conf import settings
from knowledge_base.models import ContentChunk, QueryLog
from protocol.gemini_client import GeminiClient
from protocol.faiss_driver import FAISSDriver
from .embedding_manager import EmbeddingManager
import logging
import time
from django.core.cache import cache
from celery import shared_task

logger = logging.getLogger('rag_tutor')

class RAGPipeline:
    def __init__(self):
        # Try to get cached Gemini client and FAISS index
        self.gemini_client = cache.get('gemini_client')
        self.faiss_driver = cache.get('faiss_driver')
        if not self.gemini_client or not self.faiss_driver:
            # Trigger async initialization if not present
            initialize_rag_pipeline.delay()
            # Optionally, you can raise an error or use a fallback here
            raise Exception('RAG pipeline is initializing, please try again shortly.')
        self.embedding_manager = EmbeddingManager()
    
    def query(self, 
              question: str, 
              user=None, 
              textbook_id: Optional[str] = None,
              top_k: int = 5,
              persona: str = "helpful_tutor") -> Dict[str, Any]:
        """Execute RAG query pipeline"""
        
        start_time = time.time()
        
        try:
            # Check if we have any content in the database
            total_chunks = ContentChunk.objects.count()
            if total_chunks == 0:
                # No content available, provide a helpful response
                end_time = time.time()
                response_time_ms = int((end_time - start_time) * 1000)
                
                fallback_response = self._generate_fallback_response(question, persona)
                
                query_log = QueryLog.objects.create(
                    user=user if user and getattr(user, 'is_authenticated', False) else None,
                    query_text=question,
                    query_type='rag',
                    response_text=fallback_response,
                    response_time_ms=response_time_ms
                )
                
                return {
                    'answer': fallback_response,
                    'response_time_ms': response_time_ms,
                    'sources': [],
                    'query_log_id': str(query_log.id),
                    'context_chunks': 0
                }
            
            # Check if FAISS index is empty but we have chunks
            if self.faiss_driver.index.ntotal == 0 and total_chunks > 0:
                logger.info("FAISS index is empty but chunks exist, rebuilding index...")
                self.faiss_driver.rebuild_index()
                # Refresh the driver from cache
                self.faiss_driver = cache.get('faiss_driver')
            
            # Step 1: Generate query embedding
            query_embedding = self.gemini_client.generate_embedding(question)
            
            # Step 2: Retrieve relevant chunks
            filters = {}
            if textbook_id:
                filters['textbook_id'] = textbook_id
                logger.info(f"Searching with textbook filter: {textbook_id}")
            
            similar_chunks = self.faiss_driver.search(
                query_embedding, 
                top_k=top_k,
                filters=filters
            )
            
            # Step 3: Get chunk details from database
            chunk_ids = [chunk['id'] for chunk in similar_chunks]
            chunks = ContentChunk.objects.filter(id__in=chunk_ids).select_related('textbook')
            
            # If no chunks found with textbook filter, try without filter
            if textbook_id and not chunks.exists():
                logger.info(f"No chunks found for textbook {textbook_id}, searching all content")
                similar_chunks = self.faiss_driver.search(
                    query_embedding, 
                    top_k=top_k,
                    filters={}
                )
                chunk_ids = [chunk['id'] for chunk in similar_chunks]
                chunks = ContentChunk.objects.filter(id__in=chunk_ids).select_related('textbook')
            
            # Step 4: Build context
            context = self._build_context(chunks, similar_chunks)
            
            # Step 5: Generate response
            response = self._generate_response(question, context, persona, textbook_id)
            
            # Step 6: Log query
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            query_log = QueryLog.objects.create(
                user=user if user and getattr(user, 'is_authenticated', False) else None,
                query_text=question,
                query_type='rag',
                response_text=response,
                response_time_ms=response_time_ms
            )
            if chunks.exists():
                query_log.retrieved_chunks.set(chunks)
            
            return {
                'answer': response,
                'context_chunks': len(chunks),
                'response_time_ms': response_time_ms,
                'query_log_id': str(query_log.id),
                'sources': [
                    {
                        'textbook_title': chunk.textbook.title,
                        'subject': chunk.textbook.subject.name,
                        'grade': chunk.textbook.grade.level,
                        'chunk_index': chunk.chunk_index,
                        'similarity_score': next(
                            (sc['score'] for sc in similar_chunks if sc['id'] == chunk.id), 
                            0.0
                        )
                    }
                    for chunk in chunks
                ]
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            raise
    
    def _build_context(self, chunks: List[ContentChunk], similarity_scores: List[Dict]) -> str:
        """Build context from retrieved chunks"""
        context_parts = []
        
        for chunk in chunks:
            # Find similarity score
            score = next(
                (sc['score'] for sc in similarity_scores if sc['id'] == chunk.id), 
                0.0
            )
            
            context_parts.append(f"""
Source: {chunk.textbook.title} (Grade {chunk.textbook.grade.level}, {chunk.textbook.subject.name})
Relevance: {score:.3f}
Content: {chunk.chunk_text}
---
""")
        
        return "\n".join(context_parts)
    
    def _generate_response(self, question: str, context: str, persona: str, textbook_id: Optional[str]) -> str:
        """Generate response using LLM"""
        
        # Define persona prompts
        persona_prompts = {
            "helpful_tutor": """You are a helpful and patient tutor. Explain concepts clearly and encourage learning. 
            Break down complex topics into simple steps. Use examples when helpful.""",
            
            "socratic_tutor": """You are a Socratic tutor. Instead of giving direct answers, ask guiding questions 
            that help students discover answers themselves. Encourage critical thinking.""",
            
            "encouraging_tutor": """You are an encouraging and supportive tutor. Always be positive and motivating. 
            Celebrate student progress and help build confidence while teaching.""",
            
            "strict_tutor": """You are a disciplined and structured tutor. Be precise, accurate, and methodical. 
            Focus on proper understanding and correct application of concepts."""
        }
        
        system_prompt = persona_prompts.get(persona, persona_prompts["helpful_tutor"])
        
        # Check if this is a book-specific question
        book_questions = ["what is this book about", "what is the book about", "tell me about this book", "describe this book"]
        is_book_question = any(phrase in question.lower() for phrase in book_questions)
        
        if textbook_id and is_book_question:
            # Special handling for book-specific questions
            prompt = f"""
{system_prompt}

Context from the selected textbook:
{context}

Student Question: {question}

This question is specifically about the selected textbook. Please provide a comprehensive overview of what this book covers, its main topics, and its educational focus based on the content provided. If the context doesn't give enough information about the book's overall structure, acknowledge this and describe what you can determine from the available content.

Answer:"""
        else:
            prompt = f"""
{system_prompt}

Context from textbooks:
{context}

Student Question: {question}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to fully answer the question, acknowledge this and provide what information you can.

Answer:"""
        
        return self.gemini_client.generate_chat_response(prompt)
    
    def _generate_fallback_response(self, question: str, persona: str) -> str:
        """Generate a fallback response when no content is available"""
        
        persona_prompts = {
            "helpful_tutor": """You are a helpful and patient tutor. Since no textbook content is available yet, 
            provide a general educational response and encourage the student to upload some content.""",
            
            "socratic_tutor": """You are a Socratic tutor. Since no textbook content is available yet, 
            ask the student to think about what kind of content they'd like to learn from and guide them to upload it.""",
            
            "encouraging_tutor": """You are an encouraging and supportive tutor. Since no textbook content is available yet, 
            be positive and help the student understand how to get started by uploading content.""",
            
            "strict_tutor": """You are a disciplined and structured tutor. Since no textbook content is available yet, 
            explain the importance of having content and guide the student to upload appropriate materials."""
        }
        
        system_prompt = persona_prompts.get(persona, persona_prompts["helpful_tutor"])
        
        prompt = f"""
{system_prompt}

Student Question: {question}

Please provide a helpful response explaining that no textbook content is currently available, and guide them on how to upload content to get started with the AI tutor system.

Answer:"""
        
        try:
            return self.gemini_client.generate_chat_response(prompt)
        except Exception as e:
            logger.error(f"Fallback response generation failed: {str(e)}")
            return f"I'd be happy to help you with '{question}', but I don't have any textbook content to reference yet. Please upload some educational content using the upload form above, and I'll be able to provide more specific and helpful answers based on that material!"

# Celery task to initialize and cache Gemini client and FAISS index
@shared_task
def initialize_rag_pipeline():
    from protocol.gemini_client import GeminiClient
    from protocol.faiss_driver import FAISSDriver
    gemini_client = GeminiClient()
    faiss_driver = FAISSDriver()
    cache.set('gemini_client', gemini_client, timeout=None)
    cache.set('faiss_driver', faiss_driver, timeout=None)

# Management command to pre-warm the RAG pipeline
# Place this at the end of the file
from django.core.management.base import BaseCommand
import time

class Command(BaseCommand):
    help = 'Pre-warm the RAG pipeline (Gemini and FAISS) so users never see the initializing error.'

    def handle(self, *args, **options):
        from django.core.cache import cache
        from context.rag_pipeline import initialize_rag_pipeline
        self.stdout.write('Triggering RAG pipeline initialization...')
        initialize_rag_pipeline.delay()
        timeout = 60  # seconds
        interval = 2
        waited = 0
        while waited < timeout:
            if cache.get('gemini_client') and cache.get('faiss_driver'):
                self.stdout.write(self.style.SUCCESS('RAG pipeline is ready!'))
                return
            self.stdout.write('Waiting for RAG pipeline to initialize...')
            time.sleep(interval)
            waited += interval
        self.stdout.write(self.style.ERROR('Timeout: RAG pipeline did not initialize in time.'))