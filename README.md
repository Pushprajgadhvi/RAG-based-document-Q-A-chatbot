<<<<<<< HEAD
# 🧠 RAG-Based Document Q&A Chatbot

> Upload any document (PDF, Word, TXT) and ask questions — the AI answers from YOUR file, not the internet.

**Built with:** Python · FastAPI · FAISS · SentenceTransformers · LLaMA 3 (Groq) · React · Vite

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER UPLOADS PDF                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Text Extraction │  ← pdfplumber / python-docx
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Text Chunking   │  ← 500 chars, 100 overlap
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Embeddings     │  ← all-MiniLM-L6-v2 (384-dim)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   FAISS Index    │  ← Vector Database
                    └─────────────────┘

USER ASKS QUESTION
        │
┌───────▼──────────────────────────────────────┐
│  1. Embed question → query vector             │
│  2. FAISS search → Top-K similar chunks      │
│  3. Build prompt: context + question          │
│  4. LLaMA 3 (Groq) generates grounded answer │
└───────────────────────────────────────────────┘
```

## 🧠 What is RAG?

**Retrieval-Augmented Generation** is an AI technique that:

1. **Retrieves** relevant pieces of YOUR documents (not from the internet)
2. **Augments** the LLM prompt with those pieces as context
3. **Generates** an answer grounded in your actual data

This prevents the LLM from "hallucinating" (making things up) because it only answers from what's in your files.

---

## 🗂️ Project Structure

```
rag-chatbot/
├── backend/
│   ├── main.py              # FastAPI app — full RAG pipeline
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Docker image for backend
│   └── .env.example         # Copy to .env and add API key
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main app component
│   │   ├── App.css          # All styles
│   │   └── components/
│   │       ├── ChatWindow.jsx      # Chat UI with citations
│   │       ├── DocumentUploader.jsx # Drag & drop upload
│   │       └── Sidebar.jsx         # Documents & info panel
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile           # Docker image for frontend
│   └── nginx.conf           # Nginx for serving React build
│
└── docker-compose.yml       # Run everything with one command
```

---

## 🚀 Quick Start (Local)

### Step 1 — Get a FREE Groq API Key
1. Go to **https://console.groq.com**
2. Sign up (free, no credit card)
3. Go to **API Keys** → Create Key
4. Copy the key

### Step 2 — Backend Setup

```bash
# Clone / navigate to project
cd rag-chatbot/backend

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Open .env and paste your Groq API key:
#   GROQ_API_KEY=gsk_your_key_here

# Run the backend
uvicorn main:app --reload --port 8000
```

✅ Backend running at: **http://localhost:8000**
📖 API docs at: **http://localhost:8000/docs**

### Step 3 — Frontend Setup

```bash
# In a new terminal
cd rag-chatbot/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ Frontend running at: **http://localhost:3000**

### Step 4 — Use It!
1. Open **http://localhost:3000**
2. Upload a PDF, Word doc, or TXT file
3. Wait for "Processing..." to finish
4. Ask any question about your document!

---

## 🐳 Docker Deployment (Recommended)

```bash
# From project root
cd rag-chatbot

# Add your Groq key to .env
echo "GROQ_API_KEY=your_key_here" > .env

# Build and run everything
docker-compose up --build

# App will be at http://localhost:3000
```

---

## ☁️ Deploy to Cloud

### Option A: Render.com (Free Tier Available)

**Backend:**
1. Push code to GitHub
2. Go to render.com → New Web Service
3. Connect your GitHub repo
4. Set:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variable:** `GROQ_API_KEY = your_key`

**Frontend:**
1. New Static Site on Render
2. Set:
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
   - **Environment Variable:** `VITE_API_URL = https://your-backend.onrender.com`

### Option B: Railway.app (Easiest)

```bash
# Install Railway CLI
npm install -g @railway/cli

railway login
railway init
railway up
```

---

## 🔧 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/session/new` | Create a new chat session |
| POST | `/upload/{session_id}` | Upload a document |
| POST | `/chat` | Ask a question |
| GET | `/session/{session_id}` | Get session info |
| DELETE | `/session/{session_id}` | Clear session |
| GET | `/health` | Health check |

---

## 🛠️ Tech Stack Explained

| Component | Technology | Why |
|-----------|-----------|-----|
| **API Framework** | FastAPI | Modern, fast, auto-generates API docs |
| **Embedding Model** | all-MiniLM-L6-v2 | Best speed/accuracy for semantic search |
| **Vector Database** | FAISS (Facebook) | Industry-standard, runs locally, lightning fast |
| **LLM** | LLaMA 3 8B via Groq | Free, 800 tokens/sec, no credit card |
| **PDF Parsing** | pdfplumber | Handles multi-column, tables, complex layouts |
| **Frontend** | React + Vite | Fast development, component-based UI |
| **Containerization** | Docker | Reproducible, easy deployment |

---

## 💼 CV Highlights (what to say in interviews)

- **"I built a RAG pipeline from scratch"** — text extraction → chunking → embedding → FAISS indexing → semantic retrieval → LLM generation
- **"I used FAISS for vector similarity search"** — show you know production-grade vector DBs
- **"I integrated SentenceTransformers"** — demonstrates ML model integration
- **"I used Groq's inference API"** — shows awareness of modern LLM APIs
- **"I designed a session-based multi-document architecture"** — system design thinking
- **"I containerized it with Docker"** — DevOps awareness

---

## 🔮 Possible Enhancements (mention in interviews)

- [ ] Add **Pinecone** or **Weaviate** as a cloud vector DB
- [ ] Add **OCR support** for scanned PDFs (using Tesseract)
- [ ] Add **streaming responses** with FastAPI SSE
- [ ] Add **user authentication** with JWT
- [ ] Add **conversation memory** with LangChain
- [ ] Add **re-ranking** with a cross-encoder model
- [ ] Deploy on **AWS ECS** or **Google Cloud Run**

---

## 📚 Key Concepts for Interviews

**Q: Why chunk documents?**
A: LLMs have a limited context window (~8K tokens). We can't fit a 50-page PDF. Chunking lets us only send the RELEVANT parts.

**Q: Why use vector embeddings?**
A: Keywords (like CTRL+F) miss synonyms and context. Vectors capture semantic MEANING — "car" and "automobile" are close in vector space.

**Q: What is FAISS?**
A: Facebook AI Similarity Search — an efficient library for finding nearest neighbor vectors. Used in production at Meta, Google, etc.

**Q: How does RAG prevent hallucination?**
A: The system prompt explicitly tells the LLM to ONLY answer from the provided context. If the answer isn't there, it says so.

**Q: What's the difference between RAG and fine-tuning?**
A: Fine-tuning bakes knowledge into model weights (expensive, static). RAG retrieves at runtime (cheap, updatable, explainable).
=======
# RAG-based-document-Q-A-chatbot
RAG-based document Q&amp;A chatbot
>>>>>>> 08042a98b5e23d065195100124a309ebf4f08388
