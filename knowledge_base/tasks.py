from celery import shared_task
from django.conf import settings
from knowledge_base.models import TextbookContent, ContentChunk
from context.embedding_manager import EmbeddingManager
from protocol.gemini_client import GeminiClient
from protocol.faiss_driver import FAISSDriver
import logging

logger = logging.getLogger('rag_tutor')

@shared_task
def process_textbook_content(textbook_id):
    """Process uploaded textbook content by chunking, embedding, and indexing"""
    try:
        logger.info(f"Starting processing for textbook {textbook_id}")
        textbook = TextbookContent.objects.get(id=textbook_id)
        textbook.processing_status = 'processing'
        textbook.save()

        # Clean up any existing chunks for this textbook (idempotency)
        ContentChunk.objects.filter(textbook=textbook).delete()

        # Initialize helpers
        embedding_manager = EmbeddingManager()
        gemini_client = GeminiClient()
        faiss_driver = FAISSDriver()

        # Chunk the content
        logger.info(f"Chunking content for textbook {textbook_id}")
        chunks_data = embedding_manager.chunk_text(
            textbook.content_text,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        if not chunks_data:
            raise ValueError("No chunks generated from content text.")

        # Create ContentChunk objects
        chunks = []
        for i, chunk_data in enumerate(chunks_data):
            chunk = ContentChunk.objects.create(
                textbook=textbook,
                chunk_text=chunk_data['text'],
                chunk_index=i,
                start_char=chunk_data['start'],
                end_char=chunk_data['end'],
                metadata={
                    'token_count': chunk_data['token_count'],
                    'textbook_title': textbook.title,
                    'subject': textbook.subject.name,
                    'grade': textbook.grade.level
                }
            )
            chunks.append(chunk)
        logger.info(f"Created {len(chunks)} chunks for textbook {textbook_id}")

        # Generate embeddings for all chunks
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        chunk_texts = [chunk.chunk_text for chunk in chunks]
        embeddings = gemini_client.generate_batch_embeddings(chunk_texts)
        if len(embeddings) != len(chunks):
            raise ValueError(f"Mismatch between embeddings ({len(embeddings)}) and chunks ({len(chunks)})")

        # Store embeddings in chunks and add to FAISS
        logger.info(f"Storing embeddings and adding to FAISS index")
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding_vector = embedding
            chunk.save()
        faiss_driver.add_embeddings(str(textbook_id), embeddings)

        # Update textbook status
        textbook.is_processed = True
        textbook.processing_status = 'completed'
        textbook.save()
        logger.info(f"Successfully processed textbook {textbook_id} with {len(chunks)} chunks")

        # --- NEW: Clear cache and rebuild FAISS index ---
        from django.core.cache import cache
        cache.clear()
        logger.info('Cache cleared after processing textbook')
        faiss_driver.rebuild_index()
        logger.info('FAISS index rebuilt after processing textbook')
        # --- END NEW ---

    except TextbookContent.DoesNotExist:
        logger.error(f"Textbook {textbook_id} not found")
    except Exception as e:
        logger.error(f"Error processing textbook {textbook_id}: {str(e)}", exc_info=True)
        # Update status to failed
        try:
            textbook = TextbookContent.objects.get(id=textbook_id)
            textbook.processing_status = 'failed'
            textbook.save()
        except Exception:
            pass
        raise

