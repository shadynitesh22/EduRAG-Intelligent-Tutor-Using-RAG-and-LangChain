from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Count, Avg
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import json
import logging
import psutil
import time

from knowledge_base.models import (
    TextbookContent, Subject, Grade, ContentChunk, QueryLog, 
    AuditLog, SystemMetrics
)
from knowledge_base.serializers import (
    TextbookContentSerializer, SubjectSerializer, GradeSerializer, QueryLogSerializer,
    AuditLogSerializer, SystemMetricsSerializer,
    FeedbackSubmissionSerializer, QueryAnalyticsSerializer
)
from knowledge_base.tasks import process_textbook_content
from context.rag_pipeline import RAGPipeline
from context.sql_agent import SQLAgent
from protocol.webhook_adapter import WebhookAdapter
from .tasks import send_webhook_async

logger = logging.getLogger('rag_tutor')

class TestView(APIView):
    """Simple test endpoint to verify system is working"""
    
    def get(self, request):
        return Response({
            'status': 'ok',
            'message': 'API is working!',
            'timestamp': timezone.now().isoformat(),
            'user_authenticated': request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated
        })

@method_decorator(csrf_exempt, name='dispatch')
class TextbookViewSet(viewsets.ModelViewSet):
    queryset = TextbookContent.objects.all()
    serializer_class = TextbookContentSerializer
    
    def get_queryset(self):
        return TextbookContent.objects.all().order_by('-uploaded_at')
    
    def list(self, request, *args, **kwargs):
        """Override list method to add debugging"""
        logger.info(f"TextbookViewSet.list called - user: {request.user}, authenticated: {request.user.is_authenticated if request.user else 'No user'}")
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def all_materials(self, request):
        """Get all textbooks including pending and processing ones for the materials list"""
        logger.info(f"TextbookViewSet.all_materials called - user: {request.user}")
        
        # Get all textbooks regardless of status
        qs = TextbookContent.objects.all().order_by('-uploaded_at')
        
        # For authenticated users, filter by user
        if request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            qs = qs.filter(uploaded_by=request.user)
        
        serializer = self.get_serializer(qs, many=True)
        return Response({
            'results': serializer.data,
            'count': qs.count()
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete a textbook and its associated content"""
        logger.info(f"TextbookViewSet.destroy called - user: {request.user}, authenticated: {request.user.is_authenticated if request.user else 'No user'}")
        
        try:
            instance = self.get_object()
            logger.info(f"Deleting textbook: {instance.id} - {instance.title}")
            
            # Allow deletion for demo purposes (remove authentication check)
            # In production, you would want to check user permissions here
            
            # Delete associated chunks
            ContentChunk.objects.filter(textbook=instance).delete()
            
            # Delete the textbook
            instance.delete()

            # --- NEW: Clear cache and rebuild FAISS index ---
            from protocol.faiss_driver import FAISSDriver
            from django.core.cache import cache
            cache.clear()
            logger.info('Cache cleared after deleting textbook')
            faiss = FAISSDriver()
            faiss.rebuild_index()
            logger.info('FAISS index rebuilt after deleting textbook')
            # --- END NEW ---
            
            logger.info(f"Successfully deleted textbook: {instance.id}")
            return Response(
                {'message': 'Textbook deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            logger.error(f"Failed to delete textbook: {str(e)}")
            return Response(
                {'error': 'Failed to delete textbook'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.all().order_by('name')
    serializer_class = SubjectSerializer

class GradeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Grade.objects.all().order_by('level')
    serializer_class = GradeSerializer

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class UploadContentView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload textbook content with metadata"""
        logger.info(f"UploadContentView.post called - user: {request.user}, authenticated: {request.user.is_authenticated if request.user else 'No user'}")
        
        try:
            # Log incoming request data for debugging
            logger.info(f"Upload request data: files={request.FILES}, data={request.data}")
            # Extract file and metadata
            file = request.FILES.get('file')
            title = request.data.get('title')
            subject_id = request.data.get('subject_id')
            grade_id = request.data.get('grade_id')
            
            if not all([file, title, subject_id, grade_id]):
                logger.error(f"Missing required fields: file={file}, title={title}, subject_id={subject_id}, grade_id={grade_id}")
                return Response(
                    {'error': 'Missing required fields: file, title, subject_id, grade_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate subject and grade
            try:
                subject = Subject.objects.get(id=subject_id)
                grade = Grade.objects.get(id=grade_id)
            except (Subject.DoesNotExist, Grade.DoesNotExist):
                logger.error(f"Invalid subject_id or grade_id: subject_id={subject_id}, grade_id={grade_id}")
                return Response(
                    {'error': 'Invalid subject_id or grade_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract text content from file
            try:
                content_text = self._extract_text_from_file(file)
            except Exception as e:
                logger.error(f"File extraction error: {str(e)}")
                return Response({'error': f'File extraction error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create textbook content
            try:
                textbook = TextbookContent.objects.create(
                    title=title,
                    subject=subject,
                    grade=grade,
                    file=file,
                    content_text=content_text,
                    uploaded_by=None,  # Allow anonymous uploads for demo
                    metadata=request.data.get('metadata', {})
                )
            except Exception as e:
                logger.error(f"TextbookContent create error: {str(e)}")
                return Response({'error': f'Failed to save content: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Log audit event
            self._log_audit_event(
                request, 'content_upload', 
                f"Uploaded textbook: {title}",
                {'textbook_id': str(textbook.id), 'file_size': file.size},
                related_content=textbook
            )
            
            # Queue processing task
            process_textbook_content.delay(str(textbook.id))
            
            # Send webhook
            send_webhook_async.delay('content_uploaded', {
                'textbook_id': str(textbook.id),
                'title': title,
                'subject': subject.name,
                'grade': grade.level
            })
            
            serializer = TextbookContentSerializer(textbook)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Content upload failed: {str(e)}", exc_info=True)
            self._log_audit_event(
                request, 'system_error',
                f"Content upload failed: {str(e)}",
                {'error': str(e)}
            )
            return Response(
                {'error': f'Content upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _extract_text_from_file(self, file):
        """Extract text content from uploaded file"""
        content = ""
        
        if file.name.endswith('.txt'):
            content = file.read().decode('utf-8')
        elif file.name.endswith('.pdf'):
            try:
                import PyPDF2
                import io
                # Reset file pointer
                file.seek(0)
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
            except ImportError:
                logger.warning("PyPDF2 not installed, using placeholder for PDF")
                content = "PDF content extraction requires PyPDF2 library"
            except Exception as e:
                logger.error(f"PDF extraction error: {str(e)}")
                content = f"PDF extraction failed: {str(e)}"
        elif file.name.endswith('.docx'):
            try:
                from docx import Document
                import io
                # Reset file pointer
                file.seek(0)
                doc = Document(io.BytesIO(file.read()))
                content = ""
                for paragraph in doc.paragraphs:
                    content += paragraph.text + "\n"
            except ImportError:
                logger.warning("python-docx not installed, using placeholder for DOCX")
                content = "DOCX content extraction requires python-docx library"
            except Exception as e:
                logger.error(f"DOCX extraction error: {str(e)}")
                content = f"DOCX extraction failed: {str(e)}"
        else:
            raise ValueError(f"Unsupported file type: {file.name}")
        
        return content
    
    def _log_audit_event(self, request, event_type, description, event_data, related_content=None):
        """Log audit event with system context"""
        try:
            session_key = getattr(request.session, 'session_key', '') or ''
            AuditLog.objects.create(
                user=request.user if request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated else None,
                event_type=event_type,
                event_description=description,
                event_data=event_data,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_id=session_key,
                related_content=related_content,
                memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024
            )
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AskQuestionView(APIView):
    def post(self, request):
        """Ask a question and get AI-powered response"""
        start_time = time.time()
        
        try:
            # Debug logging
            logger.info(f"Ask request data: {request.data}")
            
            question = request.data.get('question')
            query_type = request.data.get('type', 'rag')  # 'rag' or 'sql'
            textbook_id = request.data.get('textbook_id')
            persona = request.data.get('persona', 'helpful_tutor')

            # Debug logging
            logger.info(f"Parsed data: question='{question}', type='{query_type}', textbook_id='{textbook_id}', persona='{persona}'")

            # Improved error handling
            if not question or not question.strip():
                return Response(
                    {'error': 'You must enter a question before submitting.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if query_type not in ['rag', 'sql']:
                logger.error(f"Invalid query type: '{query_type}' (type: {type(query_type)})")
                return Response(
                    {'error': 'Invalid query type. Use "rag" or "sql".'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if query_type == 'rag':
                try:
                    rag_pipeline = RAGPipeline()
                except Exception as e:
                    if 'initializing' in str(e).lower():
                        return Response(
                            {'error': 'The AI system is warming up. Please wait a few seconds and try again.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE
                        )
                    return Response(
                        {'error': f'Internal error: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                result = rag_pipeline.query(
                    question=question,
                    user=request.user,
                    textbook_id=textbook_id,
                    persona=persona
                )
                
                # Enhanced logging with additional context
                query_log = QueryLog.objects.filter(
                    query_text=question,
                    user=request.user if request.user and getattr(request.user, 'is_authenticated', False) else None
                ).order_by('-created_at').first()
                
                if query_log:
                    query_log.persona_used = persona
                    query_log.subject_filter = ''  # Use empty string instead of None
                    query_log.grade_filter = ''    # Use empty string instead of None
                    query_log.user_agent = request.META.get('HTTP_USER_AGENT', '')
                    query_log.ip_address = self._get_client_ip(request)
                    query_log.save()
                
                # Log audit event (only if user is authenticated)
                if request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
                    self._log_audit_event(
                        request, 'query_execution',
                        f"RAG query executed: {question[:50]}...",
                        {
                            'query_type': 'rag',
                            'persona': persona,
                            'subject_filter': '',  # Use empty string instead of None
                            'grade_filter': '',    # Use empty string instead of None
                            'response_time_ms': result['response_time_ms']
                        },
                        related_query=query_log
                    )
                    
                    # Send webhook
                    send_webhook_async.delay('question_asked', {
                        'question': question,
                        'type': query_type,
                        'response_time_ms': result['response_time_ms']
                    })
                
                return Response(result, status=status.HTTP_200_OK)
                
            elif query_type == 'sql':
                # SQL agent
                sql_agent = SQLAgent()
                result = sql_agent.natural_language_to_sql(question)
                
                # Log query with enhanced context
                query_log = QueryLog.objects.create(
                    user=request.user if request.user and getattr(request.user, 'is_authenticated', False) else None,
                    query_text=question,
                    query_type='sql',
                    response_text=result['answer'],
                    persona_used=persona,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    ip_address=self._get_client_ip(request)
                )
                
                # Log audit event (only if user is authenticated)
                if request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
                    self._log_audit_event(
                        request, 'query_execution',
                        f"SQL query executed: {question[:50]}...",
                        {'query_type': 'sql', 'persona': persona},
                        related_query=query_log
                    )
                
                return Response(result, status=status.HTTP_200_OK)
            
            else:
                return Response(
                    {'error': 'Invalid query type. Use "rag" or "sql"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            end_time = time.time()
            execution_time = int((end_time - start_time) * 1000)
            
            logger.error(f"Question processing failed: {str(e)}")
            self._log_audit_event(
                request, 'system_error',
                f"Question processing failed: {str(e)}",
                {'error': str(e), 'execution_time_ms': execution_time}
            )
            return Response(
                {'error': 'Question processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _log_audit_event(self, request, event_type, description, event_data, related_query=None):
        """Log audit event with system context"""
        try:
            session_key = getattr(request.session, 'session_key', '') or ''
            AuditLog.objects.create(
                user=request.user if request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated else None,
                event_type=event_type,
                event_description=description,
                event_data=event_data,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_id=session_key,
                related_query=related_query,
                execution_time_ms=event_data.get('response_time_ms'),
                memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024
            )
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class FeedbackView(APIView):
    """Handle user feedback on AI responses"""
    
    def post(self, request):
        """Submit feedback for a query response"""
        try:
            # Extract feedback data
            rating = request.data.get('rating')
            comment = request.data.get('comment', '')
            response_text = request.data.get('response_text', '')
            response_time = request.data.get('response_time', 0)
            
            if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
                return Response(
                    {'error': 'Valid rating (1-5) is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create a QueryLog entry for this feedback (if not already exists)
            query_log = QueryLog.objects.create(
                user=request.user if request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated else None,
                query_text="Feedback submission",  # Placeholder
                query_type='rag',
                response_text=response_text,
                response_time_ms=response_time,
                rating=rating,
                rating_comment=comment,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self._get_client_ip(request)
            )
            
            # Log audit event
            self._log_audit_event(
                request, 'feedback_submitted',
                f"Feedback submitted with rating {rating}/5",
                {
                    'query_id': str(query_log.id),
                    'rating': rating,
                    'comment': comment,
                    'response_time': response_time
                },
                related_query=query_log
            )
            
            # Send webhook for feedback
            send_webhook_async.delay('feedback_submitted', {
                'query_id': str(query_log.id),
                'rating': rating,
                'comment': comment
            })
            
            return Response({
                'success': True,
                'message': 'Feedback submitted successfully',
                'query_log_id': str(query_log.id)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Feedback submission failed: {str(e)}")
            return Response(
                {'error': 'Feedback submission failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """Get chat history with optional filtering"""
        try:
            # Get filter parameters
            date_filter = request.query_params.get('date_filter', 'all')
            limit = int(request.query_params.get('limit', 50))
            
            # Build queryset
            queryset = QueryLog.objects.all().order_by('-created_at')
            
            # Apply date filter
            if date_filter == 'today':
                queryset = queryset.filter(created_at__date=timezone.now().date())
            elif date_filter == 'week':
                queryset = queryset.filter(created_at__gte=timezone.now() - timedelta(days=7))
            elif date_filter == 'month':
                queryset = queryset.filter(created_at__gte=timezone.now() - timedelta(days=30))
            
            # Limit results
            queryset = queryset[:limit]
            
            # Serialize results
            results = []
            for query in queryset:
                results.append({
                    'id': str(query.id),
                    'query_text': query.query_text,
                    'response_text': query.response_text,
                    'rating': query.rating,
                    'rating_comment': query.rating_comment,
                    'response_time': query.response_time_ms,
                    'created_at': query.created_at.isoformat(),
                    'persona_used': query.persona_used,
                    'subject_filter': query.subject_filter,
                    'grade_filter': query.grade_filter
                })
            
            return Response({
                'results': results,
                'count': len(results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to retrieve chat history: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve chat history'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _log_audit_event(self, request, event_type, description, event_data, related_query=None):
        """Log audit event"""
        try:
            session_key = getattr(request.session, 'session_key', '') or ''
            AuditLog.objects.create(
                user=request.user if request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated else None,
                event_type=event_type,
                event_description=description,
                event_data=event_data,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_id=session_key,
                related_query=related_query
            )
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AuditView(APIView):
    """Audit log viewing and analytics"""
    
    def get(self, request):
        """Get audit logs with filtering"""
        try:
            # Get filter parameters
            event_type = request.query_params.get('event_type')
            user_id = request.query_params.get('user_id')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            limit = int(request.query_params.get('limit', 100))
            
            # Build queryset
            queryset = AuditLog.objects.all()
            
            if event_type:
                queryset = queryset.filter(event_type=event_type)
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)
            
            # Limit results
            queryset = queryset[:limit]
            
            serializer = AuditLogSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve audit logs'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AnalyticsView(APIView):
    """Comprehensive analytics and metrics"""
    
    def get(self, request):
        """Get comprehensive analytics"""
        try:
            # Get time range (default: last 30 days)
            days = int(request.query_params.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            # Query analytics
            queries = QueryLog.objects.filter(created_at__gte=start_date)
            total_queries = queries.count()
            
            # Average response time
            avg_response_time = queries.aggregate(
                avg_time=Avg('response_time_ms')
            )['avg_time'] or 0
            
            # Average rating
            # The original code had UserFeedback.objects.filter(query_log__created_at__gte=start_date)
            # Since UserFeedback is removed, this will now return an empty queryset or raise an error.
            # Assuming the intent was to remove this functionality or replace it with a placeholder.
            # For now, we'll set avg_rating to 0.
            avg_rating = 0
            
            # Top personas
            top_personas = queries.values('persona_used').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            # Top subjects
            top_subjects = queries.values('subject_filter').annotate(
                count=Count('id')
            ).filter(subject_filter__isnull=False).exclude(
                subject_filter=''
            ).order_by('-count')[:5]
            
            # Feedback distribution
            # The original code had UserFeedback.objects.values('rating').annotate(count=Count('id')).order_by('rating')
            # Since UserFeedback is removed, this will now return an empty queryset or raise an error.
            # Assuming the intent was to remove this functionality or replace it with a placeholder.
            # For now, we'll set feedback_distribution to an empty dict.
            feedback_distribution = {}
            
            # Daily queries
            daily_queries = queries.extra(
                select={'day': 'date(created_at)'}
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')
            
            # System metrics
            system_metrics = self._get_system_metrics()
            
            analytics_data = {
                'total_queries': total_queries,
                'avg_response_time': round(avg_response_time, 2),
                'avg_rating': round(avg_rating, 2),
                'top_personas': list(top_personas),
                'top_subjects': list(top_subjects),
                'feedback_distribution': feedback_distribution,
                'daily_queries': list(daily_queries),
                'system_metrics': system_metrics
            }
            
            return Response(analytics_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to generate analytics: {str(e)}")
            return Response(
                {'error': 'Failed to generate analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_system_metrics(self):
        """Get current system performance metrics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Handle open files safely
            try:
                open_files = len(process.open_files())
            except (psutil.AccessDenied, psutil.ZombieProcess, ValueError):
                open_files = 0
            
            return {
                'memory_usage_mb': round(memory_info.rss / 1024 / 1024, 2),
                'cpu_percent': process.cpu_percent(),
                'thread_count': process.num_threads(),
                'open_files': open_files,
                'connections': 0  # Simplified to avoid unpacking issues
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return {}

class TopicsView(APIView):
    def get(self, request):
        """Get topics filtered by grade or subject"""
        try:
            grade_filter = request.query_params.get('grade')
            subject_filter = request.query_params.get('subject')
            
            queryset = TextbookContent.objects.all()
            
            if grade_filter:
                queryset = queryset.filter(grade__level=grade_filter)
            if subject_filter:
                queryset = queryset.filter(subject__name__icontains=subject_filter)
            
            # Group by subject and grade
            topics = queryset.values('subject__name', 'grade__level').annotate(
                count=Count('id')
            ).order_by('subject__name', 'grade__level')
            
            return Response(list(topics), status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to retrieve topics: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve topics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class MetricsView(APIView):
    def get(self, request):
        """Get system metrics and statistics"""
        try:
            # Basic counts
            total_textbooks = TextbookContent.objects.count()
            total_chunks = ContentChunk.objects.count()
            total_queries = QueryLog.objects.count()
            total_feedbacks = 0

            # If not enough data, return a friendly message
            if total_textbooks == 0 or total_chunks == 0 or total_queries == 0:
                return Response({
                    'message': 'Not enough data to display metrics yet. Please upload content and interact with the system.'
                }, status=status.HTTP_200_OK)

            # Processing status
            processing_stats = TextbookContent.objects.values('processing_status').annotate(
                count=Count('id')
            )

            # Recent activity
            recent_queries = QueryLog.objects.order_by('-created_at')[:10]
            recent_feedbacks = []

            # Average ratings
            avg_rating = 0

            metrics = {
                'total_textbooks': total_textbooks,
                'total_chunks': total_chunks,
                'total_queries': total_queries,
                'total_feedbacks': total_feedbacks,
                'avg_rating': round(avg_rating, 2),
                'processing_stats': list(processing_stats),
                'recent_queries': QueryLogSerializer(recent_queries, many=True).data,
                'recent_feedbacks': []
            }

            return Response(metrics, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to retrieve metrics: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve metrics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RAGPipelineView(APIView):
    def get(self, request):
        """Get RAG pipeline status and configuration"""
        try:
            from django.conf import settings
            
            pipeline_config = {
                'embedding_model': settings.EMBEDDING_MODEL,
                'chat_model': settings.CHAT_MODEL,
                'chunk_size': settings.CHUNK_SIZE,
                'chunk_overlap': settings.CHUNK_OVERLAP,
                'top_k_results': settings.TOP_K_RESULTS,
                'vector_db_path': settings.VECTOR_DB_PATH,
                'faiss_index_path': settings.FAISS_INDEX_PATH
            }
            
            return Response(pipeline_config, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to retrieve pipeline config: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve pipeline config'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Test RAG pipeline with a sample query"""
        try:
            test_question = request.data.get('question', 'What is the capital of France?')
            
            rag_pipeline = RAGPipeline()
            result = rag_pipeline.query(
                question=test_question,
                user=request.user,
                top_k=3
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Pipeline test failed: {str(e)}")
            return Response(
                {'error': 'Pipeline test failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SessionStatsView(APIView):
    """Get session statistics for the current user"""
    
    def get(self, request):
        try:
            # Calculate real stats from the database
            from django.db.models import Avg, Count
            from datetime import datetime, timedelta
            
            # Get session start time (last 24 hours for demo purposes)
            # In production, you might want to track actual session start
            session_start = datetime.now() - timedelta(hours=24)
            
            # Get queries from the session period
            session_queries = QueryLog.objects.filter(
                created_at__gte=session_start
            )
            
            # If no session queries, try today's queries
            if not session_queries.exists():
                today = datetime.now().date()
                session_queries = QueryLog.objects.filter(
                    created_at__date=today
                )
            
            # If still no queries, try all queries (for demo purposes)
            if not session_queries.exists():
                session_queries = QueryLog.objects.all()
            
            # Calculate stats
            questions_asked = session_queries.count()
            
            # Average response time
            avg_response_time = session_queries.aggregate(
                avg_time=Avg('response_time_ms')
            )['avg_time'] or 0
            
            # Average rating (from queries with ratings)
            rated_queries = session_queries.filter(rating__isnull=False)
            avg_rating = rated_queries.aggregate(
                avg_rating=Avg('rating')
            )['avg_rating'] or 0
            
            # Sources used (queries with retrieved chunks)
            sources_used = session_queries.filter(
                retrieved_chunks__isnull=False
            ).distinct().count()
            
            # Debug logging
            logger.info(f"Session stats calculated: questions={questions_asked}, avg_time={avg_response_time}, avg_rating={avg_rating}, sources={sources_used}")
            
            stats = {
                'total_questions': questions_asked,
                'avg_response_time': int(avg_response_time),
                'avg_rating': round(avg_rating, 1),
                'total_sources': sources_used
            }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {str(e)}")
            return Response(
                {'error': 'Failed to get session stats'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class WebhookView(APIView):
    def post(self, request):
        """Handle incoming webhooks"""
        try:
            # Verify webhook signature (implement as needed)
            # signature = request.headers.get('X-Webhook-Signature')
            
            webhook_data = request.data
            webhook_type = webhook_data.get('type')
            
            # Log webhook
            AuditLog.objects.create(
                event_type='webhook_received',
                event_description=f"Webhook received: {webhook_type}",
                event_data=webhook_data,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Process webhook based on type
            if webhook_type == 'feedback_submitted':
                # Handle feedback webhook
                pass
            elif webhook_type == 'content_uploaded':
                # Handle content upload webhook
                pass
            
            return Response({'status': 'webhook processed'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return Response(
                {'error': 'Webhook processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ManageDataView(APIView):
    """API endpoints for managing subjects and grades"""
    
    def post(self, request):
        """Add new subject or grade"""
        try:
            data_type = request.data.get('type')  # 'subject' or 'grade'
            
            if data_type == 'subject':
                name = request.data.get('name')
                description = request.data.get('description', '')
                
                if not name:
                    return Response(
                        {'error': 'Subject name is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                subject, created = Subject.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
                
                if not created:
                    return Response(
                        {'error': 'Subject already exists'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                return Response({
                    'id': subject.id,
                    'name': subject.name,
                    'description': subject.description
                }, status=status.HTTP_201_CREATED)
                
            elif data_type == 'grade':
                name = request.data.get('name')
                level = request.data.get('level')
                description = request.data.get('description', '')
                
                if not name or not level:
                    return Response(
                        {'error': 'Grade name and level are required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                grade, created = Grade.objects.get_or_create(
                    level=level,
                    defaults={'name': name, 'description': description}
                )
                
                if not created:
                    return Response(
                        {'error': 'Grade already exists'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                return Response({
                    'id': grade.id,
                    'name': grade.name,
                    'level': grade.level,
                    'description': grade.description
                }, status=status.HTTP_201_CREATED)
            
            else:
                return Response(
                    {'error': 'Invalid type. Use "subject" or "grade"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Failed to add {data_type}: {str(e)}")
            return Response(
                {'error': f'Failed to add {data_type}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request):
        """Delete subject or grade"""
        try:
            data_type = request.data.get('type')  # 'subject' or 'grade'
            item_id = request.data.get('id')
            
            if not data_type or not item_id:
                return Response(
                    {'error': 'Type and ID are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if data_type == 'subject':
                try:
                    subject = Subject.objects.get(id=item_id)
                    subject.delete()
                    return Response({'message': 'Subject deleted successfully'})
                except Subject.DoesNotExist:
                    return Response(
                        {'error': 'Subject not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
            elif data_type == 'grade':
                try:
                    grade = Grade.objects.get(id=item_id)
                    grade.delete()
                    return Response({'message': 'Grade deleted successfully'})
                except Grade.DoesNotExist:
                    return Response(
                        {'error': 'Grade not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            else:
                return Response(
                    {'error': 'Invalid type. Use "subject" or "grade"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Failed to delete {data_type}: {str(e)}")
            return Response(
                {'error': f'Failed to delete {data_type}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """Get all subjects and grades"""
        try:
            subjects = Subject.objects.all().values('id', 'name', 'description')
            grades = Grade.objects.all().values('id', 'name', 'level', 'description')
            
            return Response({
                'subjects': list(subjects),
                'grades': list(grades)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to retrieve data: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )