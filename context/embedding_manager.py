from typing import List, Dict, Any
from django.conf import settings
import tiktoken
import re

class EmbeddingManager:
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks"""
        
        # Clean and prepare text
        text = self._clean_text(text)
        
        # Split into sentences for better chunking
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            token_count = len(self.tokenizer.encode(potential_chunk))
            
            if token_count <= chunk_size:
                current_chunk = potential_chunk
            else:
                # Save current chunk if it's not empty
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'start': current_start,
                        'end': current_start + len(current_chunk),
                        'token_count': len(self.tokenizer.encode(current_chunk))
                    })
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk, chunk_overlap)
                    current_start += len(current_chunk) - len(overlap_text)
                    current_chunk = overlap_text + " " + sentence
                else:
                    # Handle case where single sentence is too long
                    current_chunk = sentence
            
        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'start': current_start,
                'end': current_start + len(current_chunk),
                'token_count': len(self.tokenizer.encode(current_chunk))
            })
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)\"\']+', ' ', text)
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved with spaCy or NLTK)
        sentence_endings = r'[.!?]+'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text for chunking"""
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= overlap_size:
            return text
        
        overlap_tokens = tokens[-overlap_size:]
        return self.tokenizer.decode(overlap_tokens)