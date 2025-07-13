#!/usr/bin/env python3
"""
Simple deployment test script to verify all imports and basic functionality.
Run this to check if everything is working before deployment.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_tutor.settings')
django.setup()

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        # Test Django imports
        from django.conf import settings
        from django.urls import reverse
        print("✅ Django imports working")
        
        # Test model imports
        from knowledge_base.models import Subject, Grade, QueryLog, TextbookContent
        print("✅ Model imports working")
        
        # Test API imports
        from api.views import TextbookViewSet, AskQuestionView
        print("✅ API view imports working")
        
        # Test protocol imports
        from protocol.llm_client import LLMClient
        from protocol.gemini_client import GeminiClient
        from protocol.faiss_driver import FAISSDriver
        print("✅ Protocol imports working")
        
        # Test task imports
        from api.tasks import process_content_task
        print("✅ Task imports working")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_settings():
    """Test Django settings"""
    print("\nTesting Django settings...")
    
    try:
        from django.conf import settings
        
        # Check critical settings
        required_settings = [
            'DATABASES',
            'INSTALLED_APPS',
            'MIDDLEWARE',
            'TEMPLATES',
            'STATIC_URL',
            'MEDIA_URL',
            'REST_FRAMEWORK',
            'CELERY_BROKER_URL',
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                print(f"✅ {setting} configured")
            else:
                print(f"❌ {setting} missing")
                return False
        
        # Check if drf_yasg is in INSTALLED_APPS
        if 'drf_yasg' in settings.INSTALLED_APPS:
            print("✅ drf_yasg configured for Swagger UI")
        else:
            print("❌ drf_yasg missing from INSTALLED_APPS")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def test_urls():
    """Test URL configuration"""
    print("\nTesting URL configuration...")
    
    try:
        from django.urls import reverse, NoReverseMatch
        
        # Test main URLs
        test_urls = [
            ('admin:index', []),
            ('tutor:index', []),
            ('tutor:analytics_dashboard', []),
        ]
        
        for url_name, args in test_urls:
            try:
                reverse(url_name, args=args)
                print(f"✅ {url_name} URL configured")
            except NoReverseMatch:
                print(f"❌ {url_name} URL not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ URL error: {e}")
        return False

def test_models():
    """Test model functionality"""
    print("\nTesting models...")
    
    try:
        from knowledge_base.models import Subject, Grade
        
        # Test model creation (without saving)
        subject = Subject(name="Test Subject")
        grade = Grade(name="Test Grade", level=10)
        
        print("✅ Model instantiation working")
        return True
        
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 EduRAG Deployment Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_settings,
        test_urls,
        test_models,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 