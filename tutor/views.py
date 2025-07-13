# tutor/views.py
import json
import time
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.sessions.models import Session
from .models import ChatSession, Question, Answer, Source, Rating, Subject, Grade
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from knowledge_base.models import Subject, Grade, QueryLog
from django.db import models

def index(request):
    # Get or create chat session
    session_id = request.session.get('chat_session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session['chat_session_id'] = session_id
    chat_session, created = ChatSession.objects.get_or_create(session_id=session_id)

    # Get recent questions for history
    recent_questions = Question.objects.filter(session=chat_session).order_by('-created_at')[:10]
    # Get session stats
    session_stats = get_session_stats(chat_session)

    # Get subjects and grades for filters
    from knowledge_base.models import Subject, Grade, TextbookContent
    subjects = Subject.objects.all().order_by('name')
    grades = Grade.objects.all().order_by('level')

    # Get uploaded materials (all for anonymous, or by user if logged in)
    if request.user.is_authenticated:
        uploaded_materials = TextbookContent.objects.filter(uploaded_by=request.user).select_related('subject', 'grade').order_by('-uploaded_at')
    else:
        uploaded_materials = TextbookContent.objects.all().select_related('subject', 'grade').order_by('-uploaded_at')

    context = {
        'session_stats': session_stats,
        'recent_questions': recent_questions,
        'subjects': subjects,
        'grades': grades,
        'uploaded_materials': uploaded_materials,
    }
    return render(request, 'tutor/chat.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def ask_question(request):
    try:
        data = json.loads(request.body)
        question_text = data.get('question', '').strip()
        persona = data.get('persona', 'helpful_tutor')
        subject_name = data.get('subject', '')
        grade_name = data.get('grade', '')
        
        if not question_text:
            return JsonResponse({'error': 'Question cannot be empty'}, status=400)
        
        # Get or create chat session
        session_id = request.session.get('chat_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['chat_session_id'] = session_id
        
        chat_session, created = ChatSession.objects.get_or_create(session_id=session_id)
        
        # Get subject and grade objects
        subject = None
        grade = None
        if subject_name:
            subject, _ = Subject.objects.get_or_create(name=subject_name)
        if grade_name:
            grade, _ = Grade.objects.get_or_create(name=grade_name, defaults={'level': 10})
        
        # Create question
        question = Question.objects.create(
            session=chat_session,
            question_text=question_text,
            persona=persona,
            subject=subject,
            grade=grade
        )
        
        # Simulate AI response (replace with actual AI integration)
        start_time = time.time()
        response_text = simulate_ai_response(question_text, persona)
        end_time = time.time()
        
        response_time_ms = int((end_time - start_time) * 1000)
        
        # Create answer
        answer = Answer.objects.create(
            question=question,
            answer_text=response_text,
            response_time_ms=response_time_ms,
            retrieved_chunks=3  # Simulated
        )
        
        # Create sample sources (replace with actual sources)
        sample_sources = create_sample_sources(answer, subject_name, grade_name)
        
        # Prepare response
        response_data = {
            'response': response_text,
            'response_time_ms': response_time_ms,
            'retrieved_chunks': 3,
            'sources': [
                {
                    'textbook_title': source.textbook_title,
                    'subject': source.subject,
                    'grade': source.grade,
                    'similarity_score': source.similarity_score
                } for source in sample_sources
            ]
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def chat_history(request):
    session_id = request.session.get('chat_session_id')
    if not session_id:
        return JsonResponse({'history': []})
    
    try:
        chat_session = ChatSession.objects.get(session_id=session_id)
        questions = Question.objects.filter(session=chat_session).order_by('-created_at')[:20]
        
        history = []
        for question in questions:
            try:
                answer = question.answer
                history.append({
                    'question': question.question_text,
                    'response': answer.answer_text,
                    'persona': question.persona,
                    'subject': question.subject.name if question.subject else '',
                    'grade': question.grade.name if question.grade else '',
                    'timestamp': question.created_at.isoformat(),
                    'response_time': answer.response_time_ms
                })
            except Answer.DoesNotExist:
                continue
        
        return JsonResponse({'history': history})
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'history': []})

@csrf_exempt
@require_http_methods(["POST"])
def clear_chat(request):
    session_id = request.session.get('chat_session_id')
    if session_id:
        try:
            chat_session = ChatSession.objects.get(session_id=session_id)
            # Delete all questions and answers for this session
            Question.objects.filter(session=chat_session).delete()
            return JsonResponse({'success': True})
        except ChatSession.DoesNotExist:
            pass
    
    return JsonResponse({'success': True})

@csrf_exempt
@require_http_methods(["POST"])
def submit_rating(request):
    try:
        data = json.loads(request.body)
        answer_id = data.get('answer_id')
        rating_value = data.get('rating')
        
        if not answer_id or not rating_value:
            return JsonResponse({'error': 'Missing answer_id or rating'}, status=400)
        
        answer = Answer.objects.get(id=answer_id)
        rating, created = Rating.objects.update_or_create(
            answer=answer,
            defaults={'rating': rating_value}
        )
        
        return JsonResponse({'success': True})
        
    except Answer.DoesNotExist:
        return JsonResponse({'error': 'Answer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_session_stats(chat_session):
    questions = Question.objects.filter(session=chat_session)
    answers = Answer.objects.filter(question__session=chat_session)
    ratings = Rating.objects.filter(answer__question__session=chat_session)
    
    total_questions = questions.count()
    avg_response_time = answers.aggregate(avg_time=models.Avg('response_time_ms'))['avg_time'] or 0
    avg_rating = ratings.aggregate(avg_rating=models.Avg('rating'))['avg_rating'] or 0
    total_sources = Source.objects.filter(answer__question__session=chat_session).count()
    
    return {
        'questions_asked': total_questions,
        'avg_response_time': int(avg_response_time),
        'avg_rating': round(avg_rating, 1),
        'sources_used': total_sources
    }

def simulate_ai_response(question, persona):
    """Simulate AI response based on persona (replace with actual AI integration)"""
    responses = {
        'helpful_tutor': f"I'd be happy to help you with that! {question}",
        'socratic_tutor': f"That's an interesting question. What do you think about {question}?",
        'expert_tutor': f"From an expert perspective, regarding {question}...",
        'friendly_tutor': f"Hey there! Great question about {question}!"
    }
    
    time.sleep(1)  # Simulate processing time
    return responses.get(persona, "I'll help you with that question.")

def create_sample_sources(answer, subject_name, grade_name):
    """Create sample sources (replace with actual source retrieval)"""
    sources = []
    sample_data = [
        {'title': 'Mathematics Textbook', 'subject': subject_name or 'Mathematics', 'score': 0.85},
        {'title': 'Science Fundamentals', 'subject': subject_name or 'Science', 'score': 0.78},
        {'title': 'Study Guide', 'subject': subject_name or 'General', 'score': 0.72},
    ]
    
    for data in sample_data:
        source = Source.objects.create(
            answer=answer,
            textbook_title=data['title'],
            subject=data['subject'],
            grade=grade_name or 'Grade 10',
            similarity_score=data['score'],
            content="Sample content..."
        )
        sources.append(source)
    
    return sources

@login_required
def interactive_playground(request):
    """Enhanced interactive playground with feedback and audit features"""
    
    # Get subjects and grades for filters
    subjects = Subject.objects.all().order_by('name')
    grades = Grade.objects.all().order_by('level')
    
    # Get uploaded materials for the user
    from knowledge_base.models import TextbookContent
    uploaded_materials = TextbookContent.objects.filter(
        uploaded_by=request.user
    ).select_related('subject', 'grade').order_by('-uploaded_at')
    
    # Get recent questions for history
    recent_questions = QueryLog.objects.filter(
        user=request.user
    ).select_related('user').order_by('-created_at')[:10]
    
    # Calculate session statistics
    user_queries = QueryLog.objects.filter(user=request.user)
    
    session_stats = {
        'questions_asked': user_queries.count(),
        'avg_response_time': user_queries.aggregate(
            avg_time=Avg('response_time_ms')
        )['avg_time'] or 0,
        'avg_rating': QueryLog.objects.filter(
            user=request.user
        ).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0,
        'sources_used': user_queries.aggregate(
            total_sources=Count('retrieved_chunks')
        )['total_sources'] or 0
    }
    
    context = {
        'subjects': subjects,
        'grades': grades,
        'uploaded_materials': uploaded_materials,
        'recent_questions': recent_questions,
        'session_stats': session_stats,
    }
    
    return render(request, 'tutor/chat.html', context)

@login_required
def analytics_dashboard(request):
    """Analytics dashboard for viewing feedback and audit data"""
    
    # Get user's analytics
    user_queries = QueryLog.objects.filter(user=request.user)
    user_feedbacks = QueryLog.objects.filter(user=request.user)
    
    # Calculate analytics
    analytics = {
        'total_queries': user_queries.count(),
        'total_feedbacks': user_feedbacks.count(),
        'avg_rating': user_feedbacks.aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0,
        'avg_response_time': user_queries.aggregate(
            avg_time=Avg('response_time_ms')
        )['avg_time'] or 0,
        'top_personas': user_queries.values('persona_used').annotate(
            count=Count('id')
        ).order_by('-count')[:5],
        'top_subjects': user_queries.values('subject_filter').annotate(
            count=Count('id')
        ).filter(subject_filter__isnull=False).exclude(
            subject_filter=''
        ).order_by('-count')[:5],
        'feedback_distribution': user_feedbacks.values('rating').annotate(
            count=Count('id')
        ).order_by('rating'),
        'recent_activity': user_queries.order_by('-created_at')[:20]
    }
    
    context = {
        'analytics': analytics,
        'user': request.user
    }
    
    return render(request, 'tutor/analytics.html', context)