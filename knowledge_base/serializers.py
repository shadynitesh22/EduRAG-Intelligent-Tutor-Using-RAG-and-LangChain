# rag_tutor/knowledge_base/serializers.py
from rest_framework import serializers
from .models import (
    TextbookContent, Subject, Grade, ContentChunk, QueryLog, 
    AuditLog, SystemMetrics
)

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'

class ContentChunkSerializer(serializers.ModelSerializer):
    textbook_title = serializers.CharField(source='textbook.title', read_only=True)
    
    class Meta:
        model = ContentChunk
        fields = [
            'id', 'textbook', 'textbook_title', 'chunk_text', 'chunk_index',
            'start_char', 'end_char', 'metadata', 'created_at'
        ]

class TextbookContentSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    grade = GradeSerializer(read_only=True)
    uploaded_by = serializers.CharField(source='uploaded_by.username', read_only=True)
    chunks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TextbookContent
        fields = [
            'id', 'title', 'subject', 'grade', 'file', 'content_text',
            'metadata', 'uploaded_by', 'uploaded_at', 'is_processed',
            'processing_status', 'chunks_count'
        ]
    
    def get_chunks_count(self, obj):
        return obj.chunks.count()

class QueryLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    retrieved_chunks = ContentChunkSerializer(many=True, read_only=True)
    
    def get_user(self, obj):
        return obj.user.username if obj.user else 'Anonymous'
    
    class Meta:
        model = QueryLog
        fields = [
            'id', 'user', 'query_text', 'query_type', 'response_text',
            'retrieved_chunks', 'response_time_ms', 'created_at',
            'persona_used', 'subject_filter', 'grade_filter', 'top_k_results',
            'context_chunks_count', 'user_agent', 'ip_address'
        ]

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'event_type', 'event_description', 'event_data',
            'ip_address', 'user_agent', 'session_id', 'execution_time_ms',
            'memory_usage_mb', 'related_query', 'related_content', 'created_at'
        ]
        read_only_fields = ['user', 'ip_address', 'user_agent', 'session_id']

class SystemMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemMetrics
        fields = ['id', 'metric_name', 'metric_value', 'metric_unit', 'timestamp', 'tags']

class FeedbackSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting feedback on a query response"""
    query_log_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback_type = serializers.ChoiceField(choices=[
        ('helpfulness', 'Helpfulness'),
        ('accuracy', 'Accuracy'),
        ('clarity', 'Clarity'),
        ('completeness', 'Completeness'),
        ('relevance', 'Relevance')
    ])
    feedback_text = serializers.CharField(required=False, allow_blank=True)
    is_helpful = serializers.BooleanField(required=False, allow_null=True)

class QueryAnalyticsSerializer(serializers.Serializer):
    """Serializer for query analytics and metrics"""
    total_queries = serializers.IntegerField()
    avg_response_time = serializers.FloatField()
    avg_rating = serializers.FloatField()
    top_personas = serializers.ListField(child=serializers.DictField())
    top_subjects = serializers.ListField(child=serializers.DictField())
    feedback_distribution = serializers.DictField()
    daily_queries = serializers.ListField(child=serializers.DictField())
