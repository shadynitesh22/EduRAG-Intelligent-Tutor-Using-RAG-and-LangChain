from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Grade(models.Model):
    name = models.CharField(max_length=20)
    level = models.IntegerField()
    
    def __str__(self):
        return self.name

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Session {self.session_id}"

class Question(models.Model):
    PERSONA_CHOICES = [
        ('helpful_tutor', 'Helpful Tutor'),
        ('socratic_tutor', 'Socratic Tutor'),
        ('expert_tutor', 'Expert Tutor'),
        ('friendly_tutor', 'Friendly Tutor'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    question_text = models.TextField()
    persona = models.CharField(max_length=20, choices=PERSONA_CHOICES, default='helpful_tutor')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Q: {self.question_text[:50]}..."

class Answer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    response_time_ms = models.IntegerField()
    retrieved_chunks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"A: {self.answer_text[:50]}..."

class Source(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='sources')
    textbook_title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    grade = models.CharField(max_length=20)
    similarity_score = models.FloatField()
    content = models.TextField()
    
    def __str__(self):
        return f"{self.textbook_title} - {self.subject}"

class Rating(models.Model):
    answer = models.OneToOneField(Answer, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Rating: {self.rating} stars"