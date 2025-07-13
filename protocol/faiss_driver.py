import faiss
import numpy as np
import os
import json
import pickle
from typing import List, Dict, Any, Optional
from django.conf import settings
from knowledge_base.models import ContentChunk, TextbookContent
import logging
from django.core.cache import cache
from celery import shared_task

logger = logging.getLogger('rag_tutor')

class FAISSDriver:
    def __init__(self):
        # Try to get from cache
        cached = cache.get('faiss_driver')
        if cached:
            self.index_path = cached.index_path
            self.dimension = cached.dimension
            self.index = cached.index
            self.id_mapping = cached.id_mapping
            self.metadata = cached.metadata
            return
        self.index_path = settings.FAISS_INDEX_PATH
        self.dimension = 768  # Gemini embedding dimension
        self.index = None
        self.id_mapping = {}  # Maps FAISS index to chunk IDs
        self.metadata = {}    # Stores metadata for each chunk
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Load existing index or create new one
        self._load_or_create_index()
        # Cache self for future use
        cache.set('faiss_driver', self, timeout=None)
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one"""
        try:
            if os.path.exists(f"{self.index_path}.faiss"):
                self.index = faiss.read_index(f"{self.index_path}.faiss")
                
                # Check if the loaded index has the correct dimension
                if self.index.d != self.dimension:
                    logger.warning(f"FAISS index dimension mismatch: expected {self.dimension}, got {self.index.d}. Rebuilding index.")
                    self.index = faiss.IndexFlatIP(self.dimension)
                    self.id_mapping = {}
                    self.metadata = {}
                    logger.info("Created new FAISS index with correct dimension")
                else:
                    # Load metadata
                    with open(f"{self.index_path}.metadata", 'rb') as f:
                        data = pickle.load(f)
                        self.id_mapping = data['id_mapping']
                        self.metadata = data['metadata']
                    
                    logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            else:
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                self.id_mapping = {}
                self.metadata = {}
                logger.info("Created new FAISS index")
                
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            # Create new index on failure
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_mapping = {}
            self.metadata = {}
    
    def add_embeddings(self, textbook_id: str, embeddings: List[List[float]]):
        """Add embeddings to FAISS index"""
        try:
            # Get chunks for this textbook
            chunks = ContentChunk.objects.filter(textbook_id=textbook_id).order_by('chunk_index')
            
            if len(chunks) != len(embeddings):
                raise ValueError(f"Mismatch between chunks ({len(chunks)}) and embeddings ({len(embeddings)})")
            
            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(embeddings_array)
            
            # Add to index
            start_idx = self.index.ntotal
            self.index.add(embeddings_array)
            
            # Update mappings
            for i, chunk in enumerate(chunks):
                faiss_idx = start_idx + i
                self.id_mapping[faiss_idx] = str(chunk.id)
                self.metadata[faiss_idx] = {
                    'chunk_id': str(chunk.id),
                    'textbook_id': str(chunk.textbook_id),
                    'subject': chunk.textbook.subject.name,
                    'grade': chunk.textbook.grade.level,
                    'chunk_index': chunk.chunk_index,
                    'title': chunk.textbook.title
                }
            
            # Save index
            self._save_index()
            
            logger.info(f"Added {len(embeddings)} embeddings to FAISS index")
            
        except Exception as e:
            logger.error(f"Error adding embeddings to FAISS: {str(e)}")
            raise
    
    def search(self, 
               query_embedding: List[float], 
               top_k: int = 5,
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        try:
            if self.index.ntotal == 0:
                logger.info("FAISS index is empty, returning no results")
                return []
            
            # Check query embedding dimension
            if len(query_embedding) != self.dimension:
                logger.error(f"Query embedding dimension mismatch: expected {self.dimension}, got {len(query_embedding)}")
                return []
            
            # Convert query to numpy array and normalize
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)
            
            # Search
            scores, indices = self.index.search(query_array, min(top_k * 2, self.index.ntotal))
            
            logger.info(f"FAISS search returned {len(scores[0])} results with scores: {scores[0].tolist()}")
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # Invalid index
                    continue
                
                metadata = self.metadata.get(idx, {})
                
                # Apply filters
                if filters and not self._matches_filters(metadata, filters):
                    continue
                
                results.append({
                    'id': self.id_mapping.get(idx),
                    'score': float(score),
                    'metadata': metadata
                })
                
                if len(results) >= top_k:
                    break
            
            logger.info(f"After filtering, returning {len(results)} results with scores: {[r['score'] for r in results]}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching FAISS index: {str(e)}")
            logger.error(f"FAISS search error details: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"FAISS search traceback: {traceback.format_exc()}")
            raise
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches filters"""
        for key, value in filters.items():
            if value is None:
                continue
            
            if key == 'subject' and metadata.get('subject') != value:
                return False
            elif key == 'grade' and metadata.get('grade') != value:
                return False
            elif key == 'textbook_id' and metadata.get('textbook_id') != value:
                return False
        
        return True
    
    def _save_index(self):
        """Save FAISS index and metadata"""
        try:
            faiss.write_index(self.index, f"{self.index_path}.faiss")
            
            with open(f"{self.index_path}.metadata", 'wb') as f:
                pickle.dump({
                    'id_mapping': self.id_mapping,
                    'metadata': self.metadata
                }, f)
            
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
            raise
    
    def rebuild_index(self):
        """Rebuild FAISS index from database"""
        try:
            # Create new index
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_mapping = {}
            self.metadata = {}
            
            # Get all chunks with embeddings
            chunks = ContentChunk.objects.filter(
                embedding_vector__isnull=False
            ).select_related('textbook', 'textbook__subject', 'textbook__grade')
            
            if not chunks.exists():
                logger.info("No chunks with embeddings found")
                return
            
            # Collect embeddings
            embeddings = []
            for chunk in chunks:
                embeddings.append(chunk.embedding_vector)
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)
            
            # Add to index
            self.index.add(embeddings_array)
            
            # Update mappings
            for i, chunk in enumerate(chunks):
                self.id_mapping[i] = str(chunk.id)
                self.metadata[i] = {
                    'chunk_id': str(chunk.id),
                    'textbook_id': str(chunk.textbook_id),
                    'subject': chunk.textbook.subject.name,
                    'grade': chunk.textbook.grade.level,
                    'chunk_index': chunk.chunk_index,
                    'title': chunk.textbook.title
                }
            
            # Save index
            self._save_index()
            
            logger.info(f"Rebuilt FAISS index with {len(embeddings)} vectors")
            
        except Exception as e:
            logger.error(f"Error rebuilding FAISS index: {str(e)}")
            raise
    
    def remove_textbook(self, textbook_id: str):
        """Remove all chunks for a textbook from the index"""
        # Note: FAISS doesn't support efficient removal, so we rebuild
        logger.info(f"Removing textbook {textbook_id} requires index rebuild")
        self.rebuild_index()

    def force_rebuild_index(self):
        """Force rebuild FAISS index from database and clear cache"""
        try:
            logger.info("Force rebuilding FAISS index...")
            
            # Clear cache
            cache.delete('faiss_driver')
            
            # Create new index
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_mapping = {}
            self.metadata = {}
            
            # Get all chunks with embeddings
            chunks = ContentChunk.objects.filter(
                embedding_vector__isnull=False
            ).select_related('textbook', 'textbook__subject', 'textbook__grade')
            
            if not chunks.exists():
                logger.info("No chunks with embeddings found")
                return
            
            # Collect embeddings
            embeddings = []
            for chunk in chunks:
                embeddings.append(chunk.embedding_vector)
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)
            
            # Add to index
            self.index.add(embeddings_array)
            
            # Update mappings
            for i, chunk in enumerate(chunks):
                self.id_mapping[i] = str(chunk.id)
                self.metadata[i] = {
                    'chunk_id': str(chunk.id),
                    'textbook_id': str(chunk.textbook_id),
                    'subject': chunk.textbook.subject.name,
                    'grade': chunk.textbook.grade.level,
                    'chunk_index': chunk.chunk_index,
                    'title': chunk.textbook.title
                }
            
            # Save index
            self._save_index()
            
            # Update cache
            cache.set('faiss_driver', self, timeout=None)
            
            logger.info(f"Force rebuilt FAISS index with {len(embeddings)} vectors")
            
        except Exception as e:
            logger.error(f"Error force rebuilding FAISS index: {str(e)}")
            raise