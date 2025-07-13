from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid
import json

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Grade(models.Model):
    GRADE_CHOICES = [
        ('K', 'Kindergarten'),
        ('1', 'Grade 1'),
        ('2', 'Grade 2'),
        ('3', 'Grade 3'),
        ('4', 'Grade 4'),
        ('5', 'Grade 5'),
        ('6', 'Grade 6'),
        ('7', 'Grade 7'),
        ('8', 'Grade 8'),
        ('9', 'Grade 9'),
        ('10', 'Grade 10'),
        ('11', 'Grade 11'),
        ('12', 'Grade 12'),
    ]
    
    level = models.CharField(max_length=2, choices=GRADE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"Grade {self.level}"

class TextbookContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='textbooks/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'txt', 'docx'])]
    )
    content_text = models.TextField()
    metadata = models.JSONField(default=dict)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.subject.name} - Grade {self.grade.level}"

class ContentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    textbook = models.ForeignKey(TextbookContent, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()
    start_char = models.IntegerField()
    end_char = models.IntegerField()
    embedding_vector = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['textbook', 'chunk_index']
        unique_together = ['textbook', 'chunk_index']
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.textbook.title}"

class EmbeddingModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=50)  # openai, huggingface, etc.
    model_id = models.CharField(max_length=200)
    vector_dimension = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.provider})"

class QueryLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query_text = models.TextField()
    query_type = models.CharField(
        max_length=20,
        choices=[
            ('rag', 'RAG Query'),
            ('sql', 'SQL Query'),
            ('chat', 'Chat Query'),
        ],
        default='rag'
    )
    response_text = models.TextField()
    retrieved_chunks = models.ManyToManyField(ContentChunk, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    persona_used = models.CharField(max_length=50, default='helpful_tutor')
    subject_filter = models.CharField(max_length=100, blank=True)
    grade_filter = models.CharField(max_length=10, blank=True)
    top_k_results = models.IntegerField(default=5)
    context_chunks_count = models.IntegerField(default=0)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    rating = models.IntegerField(
        choices=[
            (1, 'Poor'),
            (2, 'Fair'),
            (3, 'Good'),
            (4, 'Very Good'),
            (5, 'Excellent'),
        ],
        null=True, blank=True
    )
    rating_comment = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Query by {self.user} at {self.created_at}"

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=50)
    event_description = models.TextField()
    event_data = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    memory_usage_mb = models.FloatField(null=True, blank=True)
    related_query = models.ForeignKey(QueryLog, on_delete=models.SET_NULL, null=True, blank=True)
    related_content = models.ForeignKey(TextbookContent, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} by {self.user} at {self.created_at}"

class SystemMetrics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    tags = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.metric_unit}"