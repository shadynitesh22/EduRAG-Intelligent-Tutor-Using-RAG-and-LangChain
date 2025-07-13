from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from django.conf import settings

logger = logging.getLogger('rag_tutor')

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        pass
    
    @abstractmethod
    def generate_chat_response(self, 
                             prompt: str, 
                             max_tokens: int = 500,
                             temperature: float = 0.7,
                             system_message: Optional[str] = None) -> str:
        """Generate chat response"""
        pass
    
    @abstractmethod
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass

class GeminiClient(BaseLLMClient):
    """Google Gemini API client"""
    
    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.embedding_model = genai.get_model('embedding-001')
            self.available = True
        except Exception as e:
            logger.warning(f"Gemini client not available: {e}")
            self.available = False
    
    def generate_embedding(self, text: str) -> List[float]:
        if not self.available:
            raise Exception("Gemini client not available")
        
        try:
            result = self.embedding_model.embed_content(text.replace('\n', ' '))
            return result['values'][0]['values']
        except Exception as e:
            logger.error(f"Gemini embedding generation failed: {str(e)}")
            raise
    
    def generate_chat_response(self, 
                             prompt: str, 
                             max_tokens: int = 500,
                             temperature: float = 0.7,
                             system_message: Optional[str] = None) -> str:
        if not self.available:
            raise Exception("Gemini client not available")
        
        try:
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
            raise
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.available:
            raise Exception("Gemini client not available")
        
        embeddings = []
        for text in texts:
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Gemini batch embedding generation failed: {str(e)}")
                raise
        return embeddings

class ClaudeClient(BaseLLMClient):
    """Anthropic Claude API client"""
    
    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
            self.model = "claude-3-haiku-20240307"  # Free tier model
            self.available = True
        except Exception as e:
            logger.warning(f"Claude client not available: {e}")
            self.available = False
    
    def generate_embedding(self, text: str) -> List[float]:
        if not self.available:
            raise Exception("Claude client not available")
        
        try:
            response = self.client.embeddings.create(
                model="claude-3-haiku-20240307",
                input=text.replace('\n', ' ')
            )
            return response.embedding
        except Exception as e:
            logger.error(f"Claude embedding generation failed: {str(e)}")
            raise
    
    def generate_chat_response(self, 
                             prompt: str, 
                             max_tokens: int = 500,
                             temperature: float = 0.7,
                             system_message: Optional[str] = None) -> str:
        if not self.available:
            raise Exception("Claude client not available")
        
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude chat response generation failed: {str(e)}")
            raise
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.available:
            raise Exception("Claude client not available")
        
        embeddings = []
        for text in texts:
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Claude batch embedding generation failed: {str(e)}")
                raise
        return embeddings

class FallbackLLMClient(BaseLLMClient):
    """Fallback client that returns dummy responses"""
    
    def __init__(self):
        self.available = True
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate dummy embedding (1536-dimensional)"""
        import random
        random.seed(hash(text) % 2**32)
        return [random.uniform(-1, 1) for _ in range(1536)]
    
    def generate_chat_response(self, 
                             prompt: str, 
                             max_tokens: int = 500,
                             temperature: float = 0.7,
                             system_message: Optional[str] = None) -> str:
        """Generate dummy response"""
        return f"This is a fallback response to: {prompt[:100]}..."
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate dummy batch embeddings"""
        return [self.generate_embedding(text) for text in texts]

class LLMClient:
    """Main LLM client with fallback support"""
    
    def __init__(self):
        self.clients = []
        
        # Try to initialize clients in order of preference
        try:
            self.clients.append(GeminiClient())
        except:
            pass
        
        try:
            self.clients.append(ClaudeClient())
        except:
            pass
        
        # Always add fallback client
        self.clients.append(FallbackLLMClient())
        
        # Find first available client
        self.active_client = None
        for client in self.clients:
            if client.available:
                self.active_client = client
                logger.info(f"Using LLM client: {client.__class__.__name__}")
                break
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using the first available client"""
        if not self.active_client:
            raise Exception("No LLM client available")
        
        for client in self.clients:
            try:
                return client.generate_embedding(text)
            except Exception as e:
                logger.warning(f"Failed with {client.__class__.__name__}: {e}")
                continue
        
        raise Exception("All LLM clients failed")
    
    def generate_chat_response(self, 
                             prompt: str, 
                             max_tokens: int = 500,
                             temperature: float = 0.7,
                             system_message: Optional[str] = None) -> str:
        """Generate chat response using the first available client"""
        if not self.active_client:
            raise Exception("No LLM client available")
        
        for client in self.clients:
            try:
                return client.generate_chat_response(prompt, max_tokens, temperature, system_message)
            except Exception as e:
                logger.warning(f"Failed with {client.__class__.__name__}: {e}")
                continue
        
        raise Exception("All LLM clients failed")
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings using the first available client"""
        if not self.active_client:
            raise Exception("No LLM client available")
        
        for client in self.clients:
            try:
                return client.generate_batch_embeddings(texts)
            except Exception as e:
                logger.warning(f"Failed with {client.__class__.__name__}: {e}")
                continue
        
        raise Exception("All LLM clients failed") 