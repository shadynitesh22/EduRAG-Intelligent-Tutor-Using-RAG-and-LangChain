# EduRAG - AI-Powered Educational Tutor System

A comprehensive AI-powered educational tutoring system that uses Retrieval-Augmented Generation (RAG) to provide contextual, intelligent responses based on uploaded educational materials.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Docker & Docker Compose** (for production) - [Download Docker](https://www.docker.com/products/docker-desktop/)
- **Google Gemini API Key** - [Get API Key](https://makersuite.google.com/app/apikey)

### 🛠️ Development Setup

#### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd rag_tutor
```

#### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Set Up Environment Variables
Create a `.env` file in the project root:
```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Google Gemini API
GOOGLE_API_KEY=your-gemini-api-key-here

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# File Upload
MAX_UPLOAD_SIZE=524288000  # 500MB
```

#### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

#### 7. Start the Development Server
```bash
python manage.py runserver
```

#### 8. Access the Application
- **Main App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/docs/

### 🐳 Production Setup with Docker

#### 1. Clone and Navigate
```bash
git clone <your-repo-url>
cd rag_tutor
```

#### 2. Set Up Environment Variables
Create a `.env` file:
```bash
# Production Settings
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://user:password@db:5432/rag_tutor

# Google Gemini API
GOOGLE_API_KEY=your-gemini-api-key

# Redis
REDIS_URL=redis://redis:6379/0

# File Upload
MAX_UPLOAD_SIZE=524288000
```

#### 3. Build and Start Services
```bash
docker-compose up --build
```

#### 4. Run Migrations (First Time Only)
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

#### 5. Create Superuser (Optional)
```bash
docker-compose exec web python manage.py createsuperuser
```

#### 6. Access the Application
- **Main App**: http://localhost
- **Admin Panel**: http://localhost/admin
- **API Documentation**: http://localhost/api/docs/

### 📚 How to Use

#### 1. Upload Educational Content
1. Go to the main page
2. Click "Upload Study Material"
3. Select a PDF, DOCX, or TXT file
4. Enter title, subject, and grade
5. Click "Upload Content"
6. Wait for processing to complete

#### 2. Start Chatting
1. Once content is uploaded, the chat interface becomes active
2. Type your question in the chat box
3. Select a tutor persona (Helpful, Socratic, Encouraging, Strict)
4. Optionally filter by specific textbook
5. Click "Ask Question" or press Enter

#### 3. Rate Responses
1. After each AI response, a rating modal appears
2. Give 1-5 stars based on response quality
3. Add optional comments
4. Submit feedback to improve the system

#### 4. View Analytics
1. Check session stats in the sidebar
2. View chat history in the modal
3. Export conversation data
4. Monitor system performance

### 🔧 Troubleshooting

#### Common Issues

**1. "No module named 'google.generativeai'"**
```bash
pip install google-generativeai
```

**2. "Redis connection failed"**
```bash
# Install Redis locally
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                 # macOS
```

**3. "FAISS index not found"**
```bash
# The system will create the index automatically on first use
# If issues persist, restart the application
```

**4. "File upload fails"**
```bash
# Check file size (max 500MB)
# Ensure file format is PDF, DOCX, or TXT
# Verify write permissions in upload directory
```

**5. "API key not working"**
```bash
# Verify your Google Gemini API key is correct
# Check API quota and billing status
# Ensure the key has proper permissions
```

#### Development Commands

```bash
# Run tests
python manage.py test

# Check deployment readiness
python test_deployment_ready.py

# Clear cache
python manage.py clearcache

# Reset database (WARNING: Deletes all data)
python manage.py flush

# Collect static files
python manage.py collectstatic

# Check system health
python manage.py check --deploy
```

#### Production Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update application
git pull
docker-compose up --build -d

# Backup database
docker-compose exec db pg_dump -U postgres rag_tutor > backup.sql

# Monitor resources
docker stats
```

### 📊 System Requirements

#### Development
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **CPU**: 2 cores minimum
- **Network**: Internet connection for API calls

#### Production
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **CPU**: 4 cores minimum
- **Network**: Stable internet connection
- **SSL Certificate**: For HTTPS

### 🔐 Security Notes

1. **Never commit API keys** to version control
2. **Use strong SECRET_KEY** in production
3. **Enable HTTPS** in production
4. **Regular backups** of database
5. **Monitor logs** for suspicious activity
6. **Keep dependencies updated**

### 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the API documentation at `/api/docs/`
3. Check the logs for error messages
4. Create an issue in the repository

---

## �� Technologies Used

### Backend Technologies
- **Django 4.2.11** - Web framework for rapid development
- **PostgreSQL** - Primary database for data persistence
- **Redis** - Caching and message broker for Celery
- **Celery** - Asynchronous task processing
- **Django REST Framework** - API development and serialization

### AI & Machine Learning
- **Google Gemini AI** - Large Language Model for text generation
- **FAISS (Facebook AI Similarity Search)** - Vector database for semantic search
- **TikToken** - Tokenization for text chunking
- **NumPy** - Numerical computing for embeddings

### Frontend Technologies
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with CSS Grid, Flexbox, and custom properties
- **JavaScript (ES6+)** - Interactive functionality and API communication
- **Responsive Design** - Mobile-first approach

### File Processing
- **PyPDF2** - PDF text extraction
- **python-docx** - Microsoft Word document processing
- **File Upload Handling** - Support for large files (up to 500MB)

### DevOps & Deployment
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and static file serving
- **Gunicorn** - WSGI server for Django

### Development Tools
- **Git** - Version control
- **Python 3.11** - Programming language
- **Pip** - Package management
- **Virtual Environment** - Dependency isolation

## 🎯 What I Built

### Core Features

#### 1. **Intelligent Content Processing**
- **Multi-format Support**: Upload PDF, DOCX, and TXT files
- **Automatic Text Extraction**: Extract text from various document formats
- **Smart Chunking**: Break content into optimal chunks (200 characters) with overlap
- **Embedding Generation**: Create semantic embeddings using Google Gemini AI
- **Vector Indexing**: Store embeddings in FAISS for fast similarity search

#### 2. **Advanced RAG Pipeline**
- **Semantic Search**: Find relevant content chunks based on question similarity
- **Context Retrieval**: Retrieve multiple relevant chunks for comprehensive answers
- **AI Response Generation**: Generate contextual responses using retrieved content
- **Source Attribution**: Provide source information for all responses

#### 3. **Interactive Chat Interface**
- **Real-time Chat**: Instant question-answer interactions
- **Multiple Personas**: Choose from different tutoring styles (Helpful, Socratic, Encouraging, Strict)
- **Textbook Selection**: Filter responses by specific uploaded materials
- **Rich Text Formatting**: Support for bold, italic, lists, and structured content

#### 4. **Feedback & Rating System**
- **5-Star Rating**: Rate AI responses for quality improvement
- **Comment System**: Provide detailed feedback on responses
- **Feedback Analytics**: Track and analyze user satisfaction

#### 5. **Chat History & Analytics**
- **Session Tracking**: Monitor questions asked and response times
- **History Management**: View and filter chat history by date
- **Export Functionality**: Export chat history for analysis
- **Real-time Statistics**: Track session metrics and performance

#### 6. **Content Management**
- **Subject & Grade Management**: Organize content by educational categories
- **File Upload Interface**: Drag-and-drop file upload with progress tracking
- **Content Processing Status**: Real-time processing status updates
- **Content Deletion**: Remove uploaded materials with automatic cleanup

### Technical Architecture

#### **Database Schema**
- **TextbookContent**: Store uploaded educational materials
- **ContentChunk**: Manage text chunks with embeddings
- **QueryLog**: Track all user interactions and responses
- **AuditLog**: Comprehensive system audit trail
- **Subject/Grade**: Educational categorization system

#### **API Endpoints**
- `/api/upload-content/` - File upload and processing
- `/api/ask/` - Question answering with RAG
- `/api/feedback/` - Rating and feedback submission
- `/api/session-stats/` - Real-time session statistics
- `/api/textbooks/` - Content management
- `/api/analytics/` - System analytics and metrics

#### **Asynchronous Processing**
- **Celery Tasks**: Background processing of uploaded files
- **Redis Queue**: Reliable message queuing
- **Automatic Indexing**: FAISS index updates after content changes
- **Cache Management**: Intelligent caching for performance

#### **Security Features**
- **CSRF Protection**: Cross-site request forgery prevention
- **File Validation**: Secure file upload handling
- **Input Sanitization**: XSS prevention
- **Audit Logging**: Comprehensive security audit trail

## 🎓 Educational Features

### **Adaptive Learning**
- **Personalized Responses**: Tailor responses based on selected persona
- **Context-Aware Answers**: Provide relevant information from uploaded materials
- **Multi-Subject Support**: Handle various educational subjects and grade levels

### **User Experience**
- **Intuitive Interface**: Clean, modern design with responsive layout
- **Real-time Feedback**: Immediate response with loading indicators
- **Accessibility**: Keyboard navigation and screen reader support
- **Mobile Responsive**: Works seamlessly on all device sizes

### **Performance Optimization**
- **Vector Search**: Fast semantic similarity search using FAISS
- **Caching Strategy**: Intelligent caching for frequently accessed data
- **Asynchronous Processing**: Non-blocking file processing
- **Database Optimization**: Efficient queries and indexing

## 🚀 Deployment Ready

### **Production Features**
- **Docker Containerization**: Easy deployment and scaling
- **Environment Configuration**: Secure configuration management
- **Health Monitoring**: System health checks and monitoring
- **Error Handling**: Comprehensive error handling and logging
- **Backup Strategy**: Database backup and recovery procedures

### **Scalability**
- **Horizontal Scaling**: Support for multiple application instances
- **Load Balancing**: Nginx reverse proxy for traffic distribution
- **Database Scaling**: PostgreSQL optimization for large datasets
- **Cache Scaling**: Redis clustering for high availability

## 📊 System Capabilities

### **Content Processing**
- **File Size**: Support for files up to 500MB
- **Format Support**: PDF, DOCX, TXT files
- **Processing Speed**: Fast chunking and embedding generation
- **Quality Assurance**: Automatic content validation and error handling

### **AI Capabilities**
- **Response Quality**: High-quality, contextual responses
- **Source Accuracy**: Precise source attribution and relevance scoring
- **Multi-language Support**: Handle various languages and content types
- **Continuous Learning**: Feedback-driven system improvement

### **Analytics & Insights**
- **Usage Analytics**: Track system usage and performance
- **Quality Metrics**: Monitor response quality and user satisfaction
- **Performance Monitoring**: Real-time system performance tracking
- **User Behavior Analysis**: Understand user interaction patterns

## 🎯 Use Cases

### **Educational Institutions**
- **Classroom Support**: Supplement classroom learning with AI assistance
- **Homework Help**: Provide instant help for student questions
- **Study Aid**: Create personalized study materials and guides

### **Online Learning Platforms**
- **Course Enhancement**: Add AI-powered tutoring to existing courses
- **Personalized Learning**: Adapt content to individual student needs
- **Scalable Tutoring**: Handle large numbers of students simultaneously


## 🔧 Technical Highlights

### **Innovation Features**
- **Automatic FAISS Sync**: Self-maintaining vector index
- **Real-time Processing**: Live content processing with status updates
- **Intelligent Chunking**: Optimal text segmentation for better retrieval
- **Multi-modal Support**: Handle various content types seamlessly

### **Performance Features**
- **Sub-second Response**: Fast query processing and response generation
- **Efficient Memory Usage**: Optimized memory management for large datasets
- **Scalable Architecture**: Designed for horizontal scaling
- **High Availability**: Fault-tolerant system design

This EduRAG system represents a complete, production-ready AI-powered educational platform that combines cutting-edge AI technology with robust software engineering practices to deliver an exceptional learning experience. 