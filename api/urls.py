from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Swagger/OpenAPI imports
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = DefaultRouter()
router.register(r'textbooks', views.TextbookViewSet)
router.register(r'subjects', views.SubjectViewSet)
router.register(r'grades', views.GradeViewSet)

schema_view = get_schema_view(
    openapi.Info(
        title="RAG Tutor API",
        default_version='v1',
        description="API documentation for the RAG Tutor backend.",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', include(router.urls)),
    path('test/', views.TestView.as_view(), name='test'),
    path('upload-content/', views.UploadContentView.as_view(), name='upload-content'),
    path('ask/', views.AskQuestionView.as_view(), name='ask-question'),
    path('session-stats/', views.SessionStatsView.as_view(), name='session-stats'),
    path('topics/', views.TopicsView.as_view(), name='topics'),
    path('metrics/', views.MetricsView.as_view(), name='metrics'),
    path('pipeline/', views.RAGPipelineView.as_view(), name='pipeline'),
    path('rebuild-faiss/', views.RebuildFAISSView.as_view(), name='rebuild-faiss'),
    
    # New endpoints for feedback and audit
    path('feedback/', views.FeedbackView.as_view(), name='feedback'),
    path('audit/', views.AuditView.as_view(), name='audit'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('manage/', views.ManageDataView.as_view(), name='manage-data'),
    
    # Webhook endpoint
    path('webhook/', views.WebhookView.as_view(), name='webhook'),

    # Swagger/OpenAPI endpoints
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('schema/', schema_view.without_ui(cache_timeout=0), name='openapi-schema'),
]