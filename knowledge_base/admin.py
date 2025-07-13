from django.contrib import admin
from .models import (
    Subject, Grade, TextbookContent, ContentChunk, EmbeddingModel, 
    QueryLog, AuditLog, SystemMetrics
)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['level', 'description']
    ordering = ['level']

@admin.register(TextbookContent)
class TextbookContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'grade', 'uploaded_by', 'uploaded_at', 'is_processed', 'processing_status']
    list_filter = ['subject', 'grade', 'is_processed', 'processing_status', 'uploaded_at']
    search_fields = ['title', 'content_text']
    readonly_fields = ['id', 'uploaded_at']
    ordering = ['-uploaded_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subject', 'grade', 'uploaded_by')

@admin.register(ContentChunk)
class ContentChunkAdmin(admin.ModelAdmin):
    list_display = ['textbook', 'chunk_index', 'start_char', 'end_char', 'created_at']
    list_filter = ['textbook__subject', 'textbook__grade', 'created_at']
    search_fields = ['chunk_text', 'textbook__title']
    readonly_fields = ['id', 'created_at']
    ordering = ['textbook', 'chunk_index']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('textbook', 'textbook__subject', 'textbook__grade')

@admin.register(EmbeddingModel)
class EmbeddingModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'model_id', 'vector_dimension', 'is_active', 'created_at']
    list_filter = ['provider', 'is_active', 'created_at']
    search_fields = ['name', 'model_id']
    readonly_fields = ['created_at']

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'query_type', 'persona_used', 'response_time_ms', 'created_at']
    list_filter = ['query_type', 'persona_used', 'subject_filter', 'grade_filter', 'created_at']
    search_fields = ['query_text', 'response_text', 'user__username']
    readonly_fields = ['id', 'created_at', 'response_time_ms', 'context_chunks_count']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('user', 'query_text', 'query_type')
        return self.readonly_fields

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'ip_address', 'execution_time_ms', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['event_description', 'user__username', 'ip_address']
    readonly_fields = ['id', 'created_at', 'ip_address', 'user_agent', 'session_id']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'related_query', 'related_content')
    
    def has_add_permission(self, request):
        return False  # Audit logs should only be created by the system
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete audit logs

@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'metric_value', 'metric_unit', 'timestamp']
    list_filter = ['metric_name', 'metric_unit', 'timestamp']
    search_fields = ['metric_name']
    readonly_fields = ['id', 'timestamp']
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False  # System metrics should only be created by the system
    
    def has_change_permission(self, request, obj=None):
        return False  # System metrics should not be modified
