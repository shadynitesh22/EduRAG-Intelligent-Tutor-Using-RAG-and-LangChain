import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

@pytest.mark.django_db
class TestAPIEndpoints:
    def setup_method(self):
        self.client = APIClient()
        # Optionally create a user and authenticate if needed

    def test_topics_endpoint(self):
        url = reverse('topics')
        response = self.client.get(url)
        assert response.status_code == 200
        assert 'topics' in response.data or isinstance(response.data, list)

    def test_metrics_endpoint(self):
        url = reverse('metrics')
        response = self.client.get(url)
        assert response.status_code == 200
        assert 'total_textbooks' in response.data or 'metrics' in response.data

    def test_ask_rag(self):
        url = reverse('ask-question')
        data = {
            "question": "What is the quadratic formula?",
            "type": "rag",
            "persona": "helpful_tutor",
            "subject": "Mathematics",
            "grade": "10"
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code in [200, 201, 202]
        assert 'answer' in response.data or 'response' in response.data

    def test_ask_sql(self):
        url = reverse('ask-question')
        data = {
            "question": "How many textbooks are there for Grade 10?",
            "type": "sql"
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code in [200, 201, 202]
        assert 'answer' in response.data or 'response' in response.data

    def test_feedback_endpoint(self):
        url = reverse('feedback')
        # This test assumes a valid query_log_id exists; adjust as needed
        data = {
            "query_log_id": "dummy-uuid",
            "rating": 5,
            "feedback_type": "helpfulness",
            "feedback_text": "Great answer!",
            "is_helpful": True
        }
        response = self.client.post(url, data, format='json')
        # Accept 400 if query_log_id is invalid, else 201/200
        assert response.status_code in [200, 201, 400]

    def test_analytics_endpoint(self):
        url = reverse('analytics')
        response = self.client.get(url)
        assert response.status_code == 200 