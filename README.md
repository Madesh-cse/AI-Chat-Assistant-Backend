
# 🤖 AI Chat Assistant — Backend

A production-oriented AI assistant backend built using **FastAPI, Python, PostgreSQL, Redis, LangChain, LangGraph, Ollama, Docker, and JWT authentication**.

The backend provides authentication, conversation persistence, caching, AI tool calling, conversation memory, and real-time streaming responses.

Supported capabilities include:

- 💬 AI conversations
- ⚡ LLM response streaming
- 🔐 JWT authentication
- 🧠 Conversation memory
- 🗄️ PostgreSQL persistence
- ⚡ Redis response caching
- 🕸️ LangGraph workflows
- 🦙 Ollama LLM integration
- 🌦️ Weather data
- 📰 News search
- 📚 Wikipedia search
- 🔎 Tavily web search
- 🎬 OMDb movie data
- 🖼️ Unsplash city images
- 🧑‍💻 Stack Overflow integration
- 📝 Notion integration
- 🐳 Docker / Docker Compose
- ☁️ AWS deployment support

---

# ✨ Features

## 💬 AI Conversations

The backend handles:

- User messages
- Assistant responses
- Conversation history
- Multiple conversations
- Conversation ownership
- Persistent messages
- Follow-up question context
- Tool calls

---

## Application Image
![image alt](https://github.com/Madesh-cse/AI-Chat-Assistant-Backend/blob/06b3f80231ee22e6547e44ebe9a1383372d4c100/Screenshot%20(79).png)
![image alt](https://github.com/Madesh-cse/AI-Chat-Assistant-Backend/blob/06b3f80231ee22e6547e44ebe9a1383372d4c100/Screenshot%20(78).png)
![image alt](https://github.com/Madesh-cse/AI-Chat-Assistant-Backend/blob/06b3f80231ee22e6547e44ebe9a1383372d4c100/Screenshot%20(80).png)
![image alt](https://github.com/Madesh-cse/AI-Chat-Assistant-Backend/blob/06b3f80231ee22e6547e44ebe9a1383372d4c100/Screenshot%20(81).png)
![image alt](https://github.com/Madesh-cse/AI-Chat-Assistant-Backend/blob/06b3f80231ee22e6547e44ebe9a1383372d4c100/Screenshot%20(82).png)
![image alt](https://github.com/Madesh-cse/AI-Chat-Assistant-Backend/blob/06b3f80231ee22e6547e44ebe9a1383372d4c100/Screenshot%20(83).png)
![image alt](https://github.com/Madesh-cse/AI-Chat-Assistant-Backend/blob/06b3f80231ee22e6547e44ebe9a1383372d4c100/Screenshot%20(84).png)

## ⚡ Streaming Responses

FastAPI returns LLM output progressively using:

```python
StreamingResponse
```

The LLM is consumed through streaming:

```python
for chunk in llm_with_tools.stream(messages):
    if chunk.content:
        yield chunk.content
```

Flow:

```text
Frontend
   │
   ▼
POST /chat/stream
   │
   ▼
FastAPI
   │
   ▼
ChatService
   │
   ▼
Ollama / LangChain
   │
   ├── Chunk 1
   ├── Chunk 2
   ├── Chunk 3
   └── ...
   │
   ▼
StreamingResponse
   │
   ▼
Frontend UI
```

---

# 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| SQLAlchemy | ORM |
| PostgreSQL | Persistent database |
| Redis | Caching |
| LangChain | LLM integration |
| LangGraph | AI workflow |
| Ollama | Local LLM runtime |
| Qwen | Chat model |
| JWT | Authentication |
| Pydantic | Request validation |
| Tavily | Web search |
| NewsData | News API |
| OMDb | Movie information |
| Unsplash | Image search |
| Notion API | Workspace integration |
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |

---

# 📁 Project Structure

```text
backend/
├── app/
│   ├── core/
│   │   ├── cache.py
│   │   ├── chat_history_cache.py
│   │   ├── dependencies.py
│   │   ├── redis.py
│   │   └── security.py
│   ├── db/
│   │   └── database.py
│   ├── graph/
│   │   └── graph.py
│   ├── models/
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── message.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   └── ...
│   ├── Schemas/
│   │   └── chat.py
│   ├── services/
│   │   ├── chat_database.py
│   │   ├── chat_service.py
│   │   └── llm.py
│   ├── tools/
│   │   ├── city_image.py
│   │   ├── movie.py
│   │   ├── news.py
│   │   ├── notion.py
│   │   ├── stackoverflow.py
│   │   ├── weather.py
│   │   ├── web_search.py
│   │   └── wikipedia.py
│   └── main.py
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# ⚙️ Requirements

For local development:

- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Ollama
- Git

Optional but recommended:

- Docker
- Docker Compose

Check:

```bash
python --version
docker --version
docker compose version
```

---

# 📥 Installation

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
```

Move into backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate on Windows:

```powershell
venv\Scripts\activate
```

Activate on Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🦙 Ollama Setup

Install Ollama separately and download the required models.

Chat model:

```bash
ollama pull qwen2.5:3b
```

Embedding model if document/RAG functionality is enabled:

```bash
ollama pull nomic-embed-text
```

Verify:

```bash
ollama list
```

Ollama normally runs on:

```text
http://localhost:11434
```

When FastAPI runs inside Docker on Docker Desktop:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

---

# 🔑 Environment Variables

Create:

```text
.env
```

Never commit this file.

Example:

```env
# =========================================
# POSTGRESQL
# =========================================

POSTGRES_PASSWORD=<POSTGRES_PASSWORD>

DATABASE_URL=postgresql://postgres:<URL_ENCODED_PASSWORD>@postgres:5432/ai_chatbot

# =========================================
# REDIS
# =========================================

REDIS_URL=redis://redis:6379/0

# =========================================
# OLLAMA
# =========================================

OLLAMA_BASE_URL=http://host.docker.internal:11434

# =========================================
# JWT
# =========================================

SECRET_KEY=<STRONG_RANDOM_SECRET>

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=1440

# =========================================
# TAVILY
# =========================================

TAVILY_API_KEY=<TAVILY_API_KEY>

# =========================================
# NEWSDATA
# =========================================

NEWSDATA_API_KEY=<NEWSDATA_API_KEY>

# =========================================
# OMDB
# =========================================

OMDB_API_KEY=<OMDB_API_KEY>

# =========================================
# UNSPLASH
# =========================================

UNSPLASH_ACCESS_KEY=<UNSPLASH_ACCESS_KEY>

# =========================================
# NOTION
# =========================================

NOTION_ACCESS_TOKEN=<NOTION_ACCESS_TOKEN>
```

> Never put real secrets inside `.env.example`.

Your `.env.example` should contain only placeholders.

---

# 🔐 Important Password Encoding

If your PostgreSQL password contains special URL characters such as:

```text
@
:
/
#
%
```

they must be URL encoded inside `DATABASE_URL`.

For example:

```text
@  →  %40
```

The Docker `POSTGRES_PASSWORD` itself should contain the original password, while `DATABASE_URL` must use its encoded representation when necessary.

---

# 🚀 Development

If PostgreSQL and Redis are running locally:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

OpenAPI schema:

```text
http://localhost:8000/openapi.json
```

---

# 🏗️ Production Build

The production Uvicorn command is:

```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000
```

The Dockerfile executes:

```dockerfile
CMD [
  "uvicorn",
  "app.main:app",
  "--host",
  "0.0.0.0",
  "--port",
  "8000"
]
```

Do not enable:

```text
--reload
```

in production.

---

# 🐳 Docker

## Dockerfile

Example:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD [
  "uvicorn",
  "app.main:app",
  "--host",
  "0.0.0.0",
  "--port",
  "8000"
]
```

---

# 🐳 Docker Compose

The application uses three main backend containers:

```text
Docker Compose
│
├── ai-chat-backend
│
├── ai-chat-postgres
│
└── ai-chat-redis
```

Start development containers:

```bash
docker compose up -d
```

Build and start:

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
```

View backend logs:

```bash
docker compose logs -f backend
```

Stop:

```bash
docker compose down
```

---

# 🐳 Production Docker Compose

Validate configuration:

```bash
docker compose \
  --env-file .env \
  -f docker-compose.prod.yml \
  config
```

Start production services:

```bash
docker compose \
  --env-file .env \
  -f docker-compose.prod.yml \
  up -d
```

Check services:

```bash
docker compose \
  --env-file .env \
  -f docker-compose.prod.yml \
  ps
```

View backend logs:

```bash
docker compose \
  --env-file .env \
  -f docker-compose.prod.yml \
  logs -f backend
```

---

# 🗄️ PostgreSQL

PostgreSQL stores persistent application data.

Typical relationship:

```text
User
 │
 └── Conversation
        │
        └── Messages
```

PostgreSQL contains information such as:

- Users
- Conversations
- Messages
- Conversation metadata

The production database container uses a Docker volume:

```text
postgres_data
```

This ensures database data remains available after container restarts.

---

# ⚡ Redis

Redis is used for:

- Response caching
- Conversation-history caching
- Faster repeated queries
- Reduced PostgreSQL reads
- Reduced repeated LLM calls

Flow:

```text
Chat Request
     │
     ▼
Redis Response Cache
     │
  Cache hit?
   /      \
 YES      NO
  │        │
  ▼        ▼
Return    Load history
cache        │
             ▼
         PostgreSQL
             │
             ▼
            LLM
```

Redis data is stored using a Docker volume:

```text
redis_data
```

---

# 🧠 Conversation Memory

The backend first attempts to retrieve conversation history from Redis.

```text
Incoming Message
       │
       ▼
Redis History Cache
       │
   History found?
      /     \
    YES      NO
     │        │
     │        ▼
     │    PostgreSQL
     │        │
     └────┬───┘
          ▼
     LangChain Messages
          │
          ▼
          LLM
```

Conversation history is represented using:

- `HumanMessage`
- `AIMessage`
- `ToolMessage`
- `SystemMessage`

---

# 🔐 Authentication

The API uses JWT bearer authentication.

Flow:

```text
User
 │
 ▼
Register
 │
 ▼
Password Hashing
 │
 ▼
PostgreSQL
 │
 ▼
Login
 │
 ▼
JWT Access Token
 │
 ▼
Authorization Header
 │
 ▼
Protected Route
```

Protected requests use:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

---

# 💬 Chat Flow

```text
User Message
     │
     ▼
FastAPI Chat Router
     │
     ▼
JWT Authentication
     │
     ▼
Conversation Ownership Check
     │
     ▼
ChatService
     │
     ├──────────────┐
     │              │
     ▼              ▼
Redis Cache     PostgreSQL
     │              │
     └──────┬───────┘
            ▼
     Conversation History
            │
            ▼
       LangChain / LLM
            │
            ▼
       Tool Required?
        /         \
      YES          NO
       │            │
       ▼            │
    Tool API        │
       │            │
       ▼            │
  Tool Result       │
       │            │
       └──────┬─────┘
              ▼
          Final LLM
              │
              ▼
           Response
```

---

# ⚡ Streaming Chat Flow

Endpoint:

```http
POST /chat/stream
```

Example request:

```json
{
  "message": "Explain React with an example",
  "conversation_id": 1,
  "stack_overflow_enabled": false,
  "notion_enabled": false
}
```

The service calls:

```python
llm_with_tools.stream(messages)
```

and returns each generated chunk immediately.

```text
LLM
 │
 ├── "React"
 ├── " is"
 ├── " a"
 ├── " JavaScript"
 ├── " library"
 └── ...
 │
 ▼
StreamingResponse
 │
 ▼
Frontend
```

FastAPI response:

```python
return StreamingResponse(
    generate(),
    media_type="text/plain; charset=utf-8",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    },
)
```

---

# 🕸️ LangGraph / LLM Workflow

The application uses LangGraph and LangChain-compatible tools for AI orchestration.

```text
User
 │
 ▼
Conversation Context
 │
 ▼
LLM
 │
 ▼
Tool Needed?
 │
 ├── No ──────────────→ Stream Answer
 │
 └── Yes
      │
      ▼
   Execute Tool
      │
      ▼
   Tool Result
      │
      ▼
   Final LLM
      │
      ▼
   Stream Answer
```

---

# 🧰 AI Tools

The backend currently supports tools including:

```text
get_weather
get_city_image
get_news
search_wikipedia
web_search
get_movie
search_stackoverflow
search_notion
read_notion_page
```

---

# 🌐 Tavily Web Search

Tavily provides internet search functionality.

Environment variable:

```env
TAVILY_API_KEY=<TAVILY_API_KEY>
```

Used for:

- Web searches
- Recent technical information
- Online research
- General internet retrieval

---

# 📰 NewsData

NewsData provides current and recent news.

Environment variable:

```env
NEWSDATA_API_KEY=<NEWSDATA_API_KEY>
```

---

# 🎬 OMDb

OMDb provides movie information.

Environment variable:

```env
OMDB_API_KEY=<OMDB_API_KEY>
```

It can provide information such as:

- Movie title
- Year
- Cast
- Director
- Rating
- Plot
- Runtime

---

# 🖼️ Unsplash

Unsplash provides city and image search functionality.

Environment variable:

```env
UNSPLASH_ACCESS_KEY=<UNSPLASH_ACCESS_KEY>
```

---

# 📝 Notion

The application can access a configured Notion workspace.

Environment variable:

```env
NOTION_ACCESS_TOKEN=<NOTION_ACCESS_TOKEN>
```

Supported operations include:

```text
search_notion
read_notion_page
```

---

# 📚 Wikipedia

Wikipedia search is implemented through the application's normal tool layer.

```text
search_wikipedia
```

MCP integration is currently not required for this application.

---

# 📡 API Endpoints

## Authentication

Typical authentication routes include:

```http
POST /auth/register
POST /auth/login
```

---

## Chat

### Normal Chat

```http
POST /chat/
```

Example:

```json
{
  "message": "What is FastAPI?",
  "conversation_id": 1
}
```

### Streaming Chat

```http
POST /chat/stream
```

---

## Conversations

The conversation API includes operations similar to:

```http
POST   /conversations/
GET    /conversations/
GET    /conversations/{id}
PATCH  /conversations/{id}/title
PATCH  /conversations/{id}/pin
DELETE /conversations/{id}
```

Use Swagger for the authoritative list of currently registered routes:

```text
http://localhost:8000/docs
```

---

# ❤️ Health Check

A production deployment should provide a health endpoint such as:

```http
GET /health
```

Example response:

```json
{
  "status": "healthy"
}
```

This can later be used by:

- Docker health checks
- AWS
- Load balancers
- Monitoring systems
- GitHub Actions deployment verification

---

# 🧪 Testing

If tests are configured:

```bash
pytest
```

Verbose:

```bash
pytest -v
```

Before deployment, also verify the application starts successfully:

```bash
uvicorn app.main:app
```

---

# 🔍 Swagger API Documentation

FastAPI automatically provides interactive API documentation.

Swagger:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

OpenAPI:

```text
http://localhost:8000/openapi.json
```

---

# 🔒 Security

Production security recommendations:

- Never commit `.env`.
- Never commit real API keys.
- Use strong JWT secrets.
- Use HTTPS.
- Restrict CORS.
- Do not expose PostgreSQL publicly.
- Do not expose Redis publicly.
- Use strong PostgreSQL passwords.
- Rotate leaked or accidentally committed secrets.
- Restrict AWS Security Groups.
- Use GitHub Secrets for CI/CD credentials.

---

# 🌐 CORS

During local development:

```text
Frontend
http://localhost:3000

Backend
http://localhost:8000
```

The FastAPI CORS configuration should allow the frontend origin.

For production, restrict CORS to your deployed frontend domain.

```text
https://yourdomain.com
```

Avoid using unrestricted origins in production unless intentionally required.

---

# ☁️ Production Architecture

The planned AWS architecture is:

```text
                    Internet
                       │
                       ▼
                 Domain / HTTPS
                       │
                       ▼
                Reverse Proxy
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
        Next.js Frontend    FastAPI Backend
                                  │
                   ┌──────────────┼──────────────┐
                   │              │              │
                   ▼              ▼              ▼
               PostgreSQL       Redis          Ollama
                                  │
                                  ▼
                              AI Tools
```

---

# 🔄 GitHub Actions CI/CD

Deployment flow:

```text
Developer
    │
    ▼
git push
    │
    ▼
GitHub Repository
    │
    ▼
GitHub Actions
    │
    ├── Checkout source
    ├── Install dependencies
    ├── Run validation/tests
    ├── Build Docker image
    └── Deploy
         │
         ▼
       AWS EC2
         │
         ▼
   Docker Compose
         │
         ▼
     Production
```

Production secrets should be stored using:

```text
GitHub Actions Secrets
```

or an AWS secret-management solution.

---

# 🚀 Deployment Target

The first production deployment is designed for:

- AWS EC2
- Docker Compose
- GitHub Actions
- Nginx
- HTTPS
- PostgreSQL
- Redis

Future infrastructure can migrate to:

- Amazon RDS
- Amazon ElastiCache
- Amazon ECS / Fargate
- Amazon ECR
- AWS Secrets Manager
- CloudWatch

---

# 🛠️ Troubleshooting

## View backend logs

```bash
docker compose logs -f backend
```

## View PostgreSQL logs

```bash
docker compose logs -f postgres
```

## View Redis logs

```bash
docker compose logs -f redis
```

## Check containers

```bash
docker compose ps
```

## Test Ollama

```bash
curl http://host.docker.internal:11434/api/tags
```

## Check Swagger

```text
http://localhost:8000/docs
```

---

# 📄 License

This project is built for learning, portfolio development, and demonstration purposes.
