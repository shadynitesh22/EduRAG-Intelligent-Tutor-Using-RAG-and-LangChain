import google.generativeai as genai
from typing import List, Dict, Any, Optional
from django.conf import settings
import logging
import time
from django.core.cache import cache
from celery import shared_task
import numpy as np

logger = logging.getLogger('rag_tutor')

class DummyEmbeddingModel:
    """Dummy embedding model that returns 1536-dim vectors"""
    def embed_content(self, content, task_type=None):
        return type('obj', (object,), {'embedding': [0.0] * 1536})()
    
    def embed(self, texts):
        return {'embeddings': [[0.0] * 1536 for _ in texts]}

class GeminiClient:
    def __init__(self):
        # Try to get from cache
        cached = cache.get('gemini_client')
        if cached:
            self.model = cached.model
            self.embedding_model = cached.embedding_model
            self.available = cached.available
            return
        
        try:
            import google.generativeai as genai
            
            # Check if API key is available
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY not set, using fallback mode")
                self.available = False
                self.model = None
                self.embedding_model = DummyEmbeddingModel()
                return
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Initialize chat model
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Initialize embedding model - use the correct method for Gemini
            try:
                # Use the correct embedding model name and method
                self.embedding_model = genai.get_model('models/embedding-001')
                logger.info("Successfully initialized Gemini embedding model")
            except Exception as e1:
                logger.warning(f"Failed to get embedding model via get_model: {e1}")
                try:
                    # Alternative method
                    self.embedding_model = genai.EmbeddingModel('models/embedding-001')
                    logger.info("Successfully initialized Gemini embedding model via EmbeddingModel")
                except Exception as e2:
                    logger.warning(f"Failed to get embedding model via EmbeddingModel: {e2}")
                    # Method 3: Create a dummy embedding model
                    self.embedding_model = DummyEmbeddingModel()
                    logger.info("Using dummy embedding model")
            
            self.available = True
            # Cache self for future use
            cache.set('gemini_client', self, timeout=None)
            
        except Exception as e:
            logger.error(f"Gemini client initialization failed: {e}")
            self.available = False
            self.model = None
            self.embedding_model = DummyEmbeddingModel()

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text. If Gemini fails, returns a 1536-dim dummy vector for FAISS compatibility."""
        try:
            if not self.embedding_model:
                logger.warning("No embedding model available, using dummy embedding")
                return [0.0] * 1536
            
            # Clean text
            clean_text = text.replace('\n', ' ').strip()
            if not clean_text:
                return [0.0] * 1536
            
            # Try Gemini embedding API with the correct method
            if hasattr(self.embedding_model, 'embed_content'):
                try:
                    result = self.embedding_model.embed_content(
                        content=clean_text,
                        task_type="retrieval_document"
                    )
                    embedding = result.embedding
                    logger.info(f"Generated embedding with {len(embedding)} dimensions")
                    return embedding
                except Exception as e:
                    logger.warning(f"embed_content failed: {e}")
            
            if hasattr(self.embedding_model, 'embed'):
                try:
                    # For OpenAI-compatible API
                    result = self.embedding_model.embed([clean_text])
                    embedding = result['embeddings'][0]
                    logger.info(f"Generated embedding with {len(embedding)} dimensions via embed method")
                    return embedding
                except Exception as e:
                    logger.warning(f"embed method failed: {e}")
            
            # If we get here, try direct API call
            try:
                import google.generativeai as genai
                result = genai.embed_content(
                    model='models/embedding-001',
                    content=clean_text,
                    task_type="retrieval_document"
                )
                embedding = result['embedding']
                logger.info(f"Generated embedding with {len(embedding)} dimensions via direct API")
                return embedding
            except Exception as e:
                logger.warning(f"Direct API call failed: {e}")
            
            logger.warning("All embedding methods failed, using dummy embedding")
            return [0.0] * 1536
        except Exception as e:
            logger.error(f"Gemini embedding generation failed: {str(e)}")
            # Return a dummy embedding for now to prevent crashes
            return [0.0] * 1536  # Match FAISS index dimension

    def generate_chat_response(self, 
                             prompt: str, 
                             max_tokens: int = 500,
                             temperature: float = 0.7,
                             system_message: Optional[str] = None) -> str:
        """Generate chat response using Gemini API"""
        
        try:
            if not self.model:
                return "I'm sorry, the AI model is not available at the moment."
            
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\n{prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    'max_output_tokens': max_tokens,
                    'temperature': temperature
                }
            )
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini chat response generation failed: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request."
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                logger.info(f"Generating embedding {i+1}/{len(texts)}")
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
                # Small delay to avoid rate limits
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Batch embedding generation failed for text {i+1}: {str(e)}")
                # Use dummy embedding instead of raising
                embeddings.append([0.0] * 1536)
        
        return embeddings 