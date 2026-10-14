# Installation and Deployment Guide

## DefectMind AI

---

## Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Python | 3.11 | 3.12+ not yet tested with all dependencies |
| Node.js | 18 | v20 LTS recommended |
| npm | 9+ | Bundled with Node.js |
| Docker | 20.10+ | Optional, for containerised deployment |
| Docker Compose | v3.8 compatible | Optional |
| PostgreSQL | 15 | Optional — app uses in-memory store in demo mode |

---

## Option A — Docker Compose (Recommended)

The fastest way to run the complete stack.

### 1. Clone and configure

```bash
git clone <repository-url>
cd "Intern M2"
cp .env.example .env
```

Edit `.env` and set at minimum:
```env
# Leave blank for mock LLM mode — fully functional without an API key
OPENAI_API_KEY=
```

### 2. Start all services

```bash
docker-compose up --build
```

This starts three containers:
| Container | Port | Description |
|---|---|---|
| `frontend` | 5173 | Nginx serving the React build |
| `backend` | 8000 | FastAPI + Uvicorn |
| `postgres` | 5432 | PostgreSQL 15 database |

ChromaDB is embedded in the backend container, persisted at `/app/chroma_data` in the `chroma_data` Docker volume.

### 3. Seed the knowledge base (optional but recommended)

```bash
docker-compose exec backend python ../scripts/seed_data.py
```

Or via the API:
```bash
curl -X POST http://localhost:8000/api/knowledge-base/ingest
```

### 4. Verify

```bash
curl http://localhost:8000/api/health
# Expected: {"status":"healthy","version":"4.0.0-M4",...}
```

Open http://localhost:5173 in your browser.

> **Note on ports:** Docker Compose maps the frontend container's internal port 80 to host port `5173` (see `docker-compose.yml`). Local dev (`npm run dev`) uses port `3000` as configured in `vite.config.js`.

---

## Option B — Manual Setup (Development)

### Frontend

```bash
# From the project root
npm install
npm run dev
# Frontend: http://localhost:3000  (vite.config.js sets port: 3000)
```

For a production build:
```bash
npm run build
# Output in dist/
```

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Windows (Command Prompt):
venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: install sentence-transformers for real embeddings
# (large download ~90 MB)
pip install sentence-transformers

# Optional: install ChromaDB for real vector store
pip install chromadb==0.4.18

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# API: http://localhost:8000
# Swagger: http://localhost:8000/docs
```

The backend starts in **mock mode** when:
- `OPENAI_API_KEY` is not set → mock LLM (deterministic responses)
- `sentence-transformers` not installed → mock embeddings (seeded random vectors)
- `chromadb` not installed → mock vector store (5 hardcoded results)

All three mock modes are fully functional for development and demonstration.

### Vite Proxy Configuration

In development, Vite proxies all `/api` requests to the backend. This is configured in `vite.config.js`:

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

---

## Option C — Frontend Only (Pure Demo)

The frontend can serve entirely from the live backend without any local backend setup:

```bash
# Create .env.local in the project root:
echo "VITE_API_BASE=https://defectmind-ai.onrender.com" > .env.local

# Update src/services/api.ts to use:
const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

npm install
npm run dev
```

---

## Environment Variables

All variables are set in `.env` (copy from `.env.example`).

### Backend Variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:<password>@localhost:5432/defect_analysis` | No | PostgreSQL connection string (default uses example creds — replace in production) |
| `POSTGRES_USER` | `postgres` | Docker only | DB username |
| `POSTGRES_PASSWORD` | *(set in `.env`)* | Docker only | DB password — **never commit real passwords** |
| `POSTGRES_DB` | `defect_analysis` | Docker only | DB name |
| `POSTGRES_PORT` | `5432` | Docker only | DB port |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | No | ChromaDB persistence path |
| `OPENAI_API_KEY` | *(empty)* | No | OpenAI API key — leave empty for mock mode |
| `OPENAI_API_BASE` | `https://api.openai.com/v1` | No | OpenAI-compatible API base URL |
| `LLM_MODEL` | `gpt-4o-mini` | No | LLM model identifier |
| `LLM_MODE` | `mock` | No | `mock` or `production` |
| `LLM_TEMPERATURE` | `0.3` | No | LLM sampling temperature |
| `LLM_MAX_TOKENS` | `2000` | No | Maximum LLM response tokens |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | No | Embedding model |
| `EMBEDDING_DIMENSIONS` | `384` | No | Vector dimensions |
| `DEFAULT_TOP_K` | `5` | No | Default search top-K |
| `SIMILARITY_THRESHOLD` | `0.7` | No | Minimum similarity threshold |
| `BACKEND_HOST` | `0.0.0.0` | No | Server bind address |
| `BACKEND_PORT` | `8000` | No | Server port |
| `CORS_ORIGINS` | `http://localhost:3000,...` | No | Allowed CORS origins |
| `DEBUG` | `true` | No | Enable debug logging |

### Using a Custom LLM Provider

DefectMind AI supports any OpenAI-compatible API:

```env
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
LLM_MODE=production
```

Compatible providers include OpenAI, Azure OpenAI, OpenRouter, Ollama (local), LM Studio, and any vLLM deployment.

---

## Seeding the Knowledge Base

The knowledge base must be seeded before agents can retrieve historical evidence.

### Via script

```bash
# From project root, with backend venv active
cd backend
python ../scripts/seed_data.py
# Output: Seeding complete! 36 chunks indexed.
```

### Via API

```bash
curl -X POST http://localhost:8000/api/knowledge-base/ingest
```

### Via Docker

```bash
docker-compose exec backend python ../scripts/seed_data.py
```

The script reads `data/historical_defects.csv` (12 defects, 36 total document chunks) and loads them into ChromaDB.

---

## Running Tests

```bash
cd backend

# Full M4 test suite (104 tests)
py -3.11 -m pytest tests/test_milestone4.py -v

# All test suites
py -3.11 -m pytest tests/ -v

# Specific class
py -3.11 -m pytest tests/test_milestone4.py::TestAnalyticsEndpoints -v

# Frontend type checking
npm run typecheck

# Frontend production build
npm run build
```

---

## Deployment to Render.com

The live application is deployed on Render.com using Docker-based web services.

### Backend Deployment

1. **Create a Render Web Service**
   - Source: GitHub repository
   - Runtime: Docker
   - Root Directory: `backend`
   - Dockerfile: `backend/Dockerfile`

2. **Set environment variables in Render Dashboard:**
   ```
   OPENAI_API_KEY=your-key
   OPENAI_API_BASE=https://api.openai.com/v1
   LLM_MODEL=gpt-4o-mini
   CHROMA_PERSIST_DIR=/app/chroma_data
   DATABASE_URL=postgresql+asyncpg://...  (use Render PostgreSQL add-on)
   ```

3. **Add a Persistent Disk** for ChromaDB:
   - Mount Path: `/app/chroma_data`
   - Size: 1 GB minimum

4. **Health Check Path:** `/api/health`

5. **The Dockerfile CMD:**
   ```dockerfile
   CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
   ```
   Render injects `$PORT` automatically.

### Frontend Deployment

1. **Create a Render Static Site**
   - Source: GitHub repository
   - Build Command: `npm run build`
   - Publish Directory: `dist`

2. **Rewrite rules** (for SPA routing):
   - Source: `/*`
   - Destination: `/index.html`

3. **API proxy:** The frontend calls `/api` which must be proxied to the backend. In Render Static Sites, add a rewrite/redirect rule:
   - Source: `/api/*`
   - Destination: `https://defectmind-ai.onrender.com/api/:splat`
   - Type: Proxy

   Alternatively, set the Vite `VITE_API_BASE` environment variable to the backend URL and update `api.ts` accordingly.

### Docker Compose Deployment (Self-Hosted)

For self-hosted servers (VPS, AWS EC2, DigitalOcean Droplet):

```bash
# On server:
git clone <repository>
cd "Intern M2"
cp .env.example .env
# Edit .env

docker-compose -f docker-compose.yml up -d --build

# Tail logs
docker-compose logs -f backend

# Restart after code update
docker-compose down && docker-compose up -d --build
```

---

## Dockerfile Details

### Backend (`backend/Dockerfile`)

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only (avoids large GPU download)
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch

COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .
RUN mkdir -p /app/chroma_data /app/data

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f "http://localhost:${PORT:-8000}/api/health" || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### Frontend (`Dockerfile.frontend`)

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx (`nginx.conf`)

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;  # SPA routing
    }

    location /api/ {
        proxy_pass http://backend:8000/api/;  # Proxy to backend container
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location ~* \.(js|css|png|jpg|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";  # Cache static assets
    }
}
```

---

## Troubleshooting

### Backend won't start — `ModuleNotFoundError`

```bash
# Ensure venv is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Reinstall requirements
pip install -r requirements.txt
```

### ChromaDB `pydantic_core` error

This occurs when running with a different Python version than the venv was built for. The venv's `pydantic_core` is compiled for a specific Python minor version.

```bash
# Check which Python venv uses
venv\Scripts\python.exe --version

# If mismatch, recreate venv with the correct Python:
py -3.11 -m venv venv_311
venv_311\Scripts\activate
pip install -r requirements.txt
```

### `sentence-transformers` not installed — embedding warnings

Expected in lightweight setups. The system works with mock embeddings. To install:
```bash
pip install sentence-transformers==2.2.2
```

### PostgreSQL connection refused

The backend tolerates PostgreSQL being unavailable at startup — it uses the in-memory store. The error message in the logs is non-fatal. To suppress, either:
- Start PostgreSQL, or
- Set `DATABASE_URL` to a valid connection string in `.env`

### Vite dev server shows blank page

```bash
# Check the backend is running
curl http://localhost:8000/api/health

# Check Vite proxy in vite.config.js
# Ensure proxy target matches backend port
```

### Docker build fails — `torch` download timeout

```bash
# Increase Docker build timeout or use:
docker-compose build --no-cache backend
```

### `pytest` `--timeout` flag not recognised

```bash
# pytest-timeout not installed — remove the flag
py -3.11 -m pytest tests/test_milestone4.py -v
# (no --timeout flag needed)
```

### Render deployment — cold start delay

Render free-tier services spin down after inactivity. The first request after a cold start can take 30–60 seconds. Use the health endpoint to wake the service:

```bash
curl https://defectmind-ai.onrender.com/api/health
```

---

## Python Dependencies (`backend/requirements.txt`)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.2
python-dotenv==1.0.0
python-multipart==0.0.6
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.13.0
chromadb==0.4.18
sentence-transformers==2.2.2
numpy==1.26.2
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.23.2
python-jose[cryptography]==3.3.0
```

## Frontend Dependencies (`package.json`)

```json
{
  "dependencies": {
    "framer-motion": "^11.16.1",
    "lucide-react": "^0.294.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "recharts": "^2.10.0",
    "date-fns": "^2.30.0",
    "uuid": "^9.0.1"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.1.7",
    "@vitejs/plugin-react": "^4.3.4",
    "tailwindcss": "^4.1.7",
    "typescript": "^5.7.0",
    "vite": "^6.3.5"
  }
}
```
