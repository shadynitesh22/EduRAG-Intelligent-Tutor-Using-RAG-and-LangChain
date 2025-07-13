from django.core.management.base import BaseCommand
from protocol.faiss_driver import FAISSDriver
from knowledge_base.models import ContentChunk
from django.core.cache import cache
import logging

logger = logging.getLogger('rag_tutor')

class Command(BaseCommand):
    help = 'Rebuild FAISS index from database content'

    def handle(self, *args, **options):
        self.stdout.write('Rebuilding FAISS index...')
        
        try:
            # Clear cache
            cache.clear()
            self.stdout.write('Cache cleared')
            
            # Get chunk count
            chunk_count = ContentChunk.objects.filter(embedding_vector__isnull=False).count()
            self.stdout.write(f'Found {chunk_count} chunks with embeddings')
            
            if chunk_count == 0:
                self.stdout.write(self.style.WARNING('No chunks with embeddings found. Please upload and process some content first.'))
                return
            
            # Rebuild index
            faiss = FAISSDriver()
            faiss.rebuild_index()
            
            # Verify
            final_count = faiss.index.ntotal
            self.stdout.write(f'FAISS index rebuilt with {final_count} vectors')
            
            if final_count == chunk_count:
                self.stdout.write(self.style.SUCCESS('FAISS index successfully rebuilt and verified!'))
            else:
                self.stdout.write(self.style.ERROR(f'Warning: FAISS index has {final_count} vectors but database has {chunk_count} chunks'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error rebuilding FAISS index: {str(e)}'))
            logger.error(f'Error rebuilding FAISS index: {str(e)}') 