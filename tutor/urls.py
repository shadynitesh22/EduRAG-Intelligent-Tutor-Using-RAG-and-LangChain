from django.urls import path
from . import views

app_name = 'tutor'

urlpatterns = [
    path('', views.index, name='index'),
    path('playground/', views.interactive_playground, name='interactive_playground'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('ask/', views.ask_question, name='ask_question'),
    path('chat-history/', views.chat_history, name='chat_history'),
    path('clear-chat/', views.clear_chat, name='clear_chat'),
    path('submit-rating/', views.submit_rating, name='submit_rating'),
]