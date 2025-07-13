# EduRAG: Intelligent Tutor Using RAG and LangChain

## Overview
EduRAG is a production-ready, AI-powered tutoring backend system that leverages Retrieval-Augmented Generation (RAG), LLM APIs, and a SQL-based knowledge base to deliver smart, context-aware educational responses. Built for modularity, scalability, and real-world deployment, EduRAG supports content ingestion, semantic search, RAG-based Q&A, persona-driven responses, and more.

## Features
- **Content Upload & Knowledge Base Management**: Upload and manage textbook content with metadata (topic, title, grade).
- **Vector Embedding & Semantic Retrieval**: Generate and store embeddings for semantic search using FAISS/Chroma/PGVector.
- **RAG-Based Question Answering**: Retrieve relevant content and generate grounded answers using LLMs.
- **System Prompt & Tutor Persona**: Configurable AI personas for varied response styles.
- **Natural Language SQL Querying**: Translate user questions into SQL and return human-readable answers.
- **RESTful API**: Endpoints for content upload, Q&A, topics, metrics, feedback, and analytics.
- **Bonus**: User feedback loop, answer logging, interactive playground UI.

## Tech Stack
- **Backend**: Django (can be adapted to Flask/FastAPI)
- **LLM APIs**: OpenAI GPT, Hugging Face
- **Vector Store**: FAISS, Chroma, or PGVector
- **Database**: PostgreSQL (or SQLite for dev)
- **Task Queue**: Celery + Redis
- **Deployment**: Gunicorn, Nginx, Docker

## Setup Instructions
1. **Clone the repo**
   ```bash
   git clone <your-repo-url>
   cd edurag
   ```
2. **Configure environment variables**
   - Copy `.env.example` to `.env` and fill in your secrets.
3. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```
   - This will start the web app, Celery worker, Redis, PostgreSQL, and Nginx.
4. **Apply migrations and collect static files**
   - Handled automatically by the entrypoint script.
5. **Access the app**
   - Chat UI: [http://localhost/](http://localhost/)
   - API: [http://localhost/api/](http://localhost/api/)
   - Admin: [http://localhost/admin/](http://localhost/admin/)
   - API Docs: [http://localhost/api/docs/](http://localhost/api/docs/)

## Deployment (Production)
- **Gunicorn** serves the Django app on port 8000.
- **Nginx** proxies requests from port 80 to Gunicorn.
- **nginx.conf** is included for reference.
- Ensure all environment variables are set in production.

## API Endpoints
| Method | Endpoint           | Description                           |
|--------|--------------------|---------------------------------------|
| POST   | /api/upload-content/ | Upload textbook content               |
| POST   | /api/ask/            | Ask a question (RAG/SQL)              |
| GET    | /api/topics/         | List/filter topics                    |
| GET    | /api/metrics/        | System metrics                        |
| POST   | /api/feedback/       | Submit feedback                       |
| GET    | /api/analytics/      | Analytics dashboard                   |
| GET    | /api/docs/           | OpenAPI/Swagger UI                    |

## .env.example
- See `.env.example` for all required environment variables (DB, Redis, LLM API keys, etc).

## Testing
- Use `test_api_endpoints.http` for manual API testing.
- Automated tests: `pytest` and Django test cases (see `tests/` directory).

## Evaluation Criteria
- Content ingestion, vector search, RAG, persona, API, SQL agent, feedback, logging, analytics, deployment, and bonus features. See `QA_CHECKLIST.md` for a full list.

## Deployment Checklist
- [ ] All services run via Docker Compose
- [ ] Nginx proxies to Gunicorn
- [ ] API and UI accessible at correct URLs
- [ ] Migrations and static files handled
- [ ] All environment variables set

## License
MIT

---
**For questions or support, contact: nitesh12paudel@gmail.com** 