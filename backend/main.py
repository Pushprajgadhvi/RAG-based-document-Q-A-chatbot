"""
RAG-based Document Q&A Chatbot - Backend
=========================================
This is the brain of the application. It handles:
1. PDF/Text document ingestion
2. Text chunking (splitting docs into pieces)
3. Creating embeddings (vector representations)
4. Storing them in a vector database (FAISS)
5. Semantic search (finding relevant chunks)
6. Sending context + question to LLM for answer

What is RAG (Retrieval-Augmented Generation)?
----------------------------------------------
Instead of just asking an LLM a question blindly, we:
  Step 1: RETRIEVE relevant chunks from YOUR documents
  Step 2: AUGMENT the prompt with those chunks as context
  Step 3: GENERATE an answer grounded in your documents
This makes the AI answer from YOUR data, not just its training data.
"""

import os
import uuid
import json
import pickle
import hashlib
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
load_dotenv()

import numpy as np
import faiss
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# PDF and text extraction
import pdfplumber
import docx

# Sentence splitting & embeddings
from sentence_transformers import SentenceTransformer

# LLM via Groq (free, fast)
from groq import Groq

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="RAG Document Q&A API",
    description="Upload documents and ask questions — answers come from YOUR files.",
    version="1.0.0"
)

# Allow React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # In production, set this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
# GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")      # Set in .env file

# Configuration
# ─────────────────────────────────────────────
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

print("GROQ KEY FOUND:", bool(GROQ_API_KEY))
EMBED_MODEL  = "all-MiniLM-L6-v2"                 # Fast, accurate embedding model (384-dim)
CHUNK_SIZE   = 500                                  # Characters per chunk
CHUNK_OVERLAP = 100                                 # Overlap so we don't miss context at boundaries
TOP_K        = 5                                    # How many chunks to retrieve per question
DATA_DIR     = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# Load Models (once at startup)
# ─────────────────────────────────────────────
print("Loading embedding model... (first run downloads ~90MB)")
embedder = SentenceTransformer(EMBED_MODEL)
print(f"Embedding model loaded: {EMBED_MODEL}")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ─────────────────────────────────────────────
# In-Memory Store  (replaced by FAISS on disk)
# ─────────────────────────────────────────────
# Structure:
#   sessions[session_id] = {
#       "chunks"     : List[str],          # raw text chunks
#       "metadata"   : List[dict],         # {filename, chunk_index, char_start}
#       "index"      : faiss.IndexFlatL2,  # vector index
#       "chat_history": List[dict],        # conversation so far
#   }
sessions = {}


# ─────────────────────────────────────────────
# Pydantic Models  (request / response shapes)
# ─────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]           # which chunks were used
    session_id: str

class SessionInfo(BaseModel):
    session_id: str
    document_count: int
    chunk_count: int
    chat_history: List[dict]


# ─────────────────────────────────────────────
# Text Extraction Helpers
# ─────────────────────────────────────────────
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF file.
    pdfplumber handles tables, columns, multi-page docs.
    Returns a single string of the entire document.
    """
    import io
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from Word documents paragraph by paragraph."""
    import io
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Plain text files — just decode."""
    return file_bytes.decode("utf-8", errors="ignore")


# ─────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────
def chunk_text(text: str, filename: str) -> tuple[List[str], List[dict]]:
    """
    WHY CHUNK?
    ----------
    LLMs have a limited context window. We can't dump an entire 50-page PDF
    into the prompt. Instead, we split the document into small overlapping
    pieces (chunks), embed each piece as a vector, and only send the most
    RELEVANT chunks when the user asks a question.

    CHUNK_OVERLAP prevents important info that sits at a chunk boundary
    from being lost — the last 100 chars of one chunk repeat as the first
    100 chars of the next.
    """
    chunks   = []
    metadata = []
    start    = 0
    idx      = 0

    while start < len(text):
        end   = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            metadata.append({
                "filename"    : filename,
                "chunk_index" : idx,
                "char_start"  : start,
                "char_end"    : end,
            })
            idx += 1
        start += CHUNK_SIZE - CHUNK_OVERLAP   # slide window with overlap

    return chunks, metadata


# ─────────────────────────────────────────────
# Embedding + FAISS Index
# ─────────────────────────────────────────────
def build_faiss_index(chunks: List[str]) -> faiss.IndexFlatL2:
    """
    WHAT ARE EMBEDDINGS?
    --------------------
    An embedding converts text → a list of numbers (a vector).
    Similar sentences produce vectors that are CLOSE together in
    high-dimensional space.  We use 'all-MiniLM-L6-v2' which gives
    384-dimensional vectors — fast and accurate for semantic search.

    WHAT IS FAISS?
    --------------
    FAISS (Facebook AI Similarity Search) stores those vectors and
    lets us find the TOP-K closest vectors to a query vector in
    milliseconds — even with millions of chunks.
    """
    print(f"  Building embeddings for {len(chunks)} chunks...")
    embeddings = embedder.encode(chunks, show_progress_bar=False)
    dim        = embeddings.shape[1]           # 384

    # IndexFlatL2 = exact L2 (Euclidean) distance search — best for small corpora
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings, dtype=np.float32))
    print(f"  FAISS index built with {index.ntotal} vectors (dim={dim})")
    return index


# ─────────────────────────────────────────────
# Semantic Search (the R in RAG)
# ─────────────────────────────────────────────
def retrieve_relevant_chunks(
    question    : str,
    session     : dict,
    top_k       : int = TOP_K
) -> List[dict]:
    """
    1. Embed the question  → query_vector
    2. Search FAISS index  → nearest chunk vectors
    3. Return the actual text of those chunks + metadata

    This is the RETRIEVAL step of RAG.
    """
    query_vec = embedder.encode([question], show_progress_bar=False)
    query_vec = np.array(query_vec, dtype=np.float32)

    distances, indices = session["index"].search(query_vec, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue                          # FAISS returns -1 when not enough chunks
        results.append({
            "text"       : session["chunks"][idx],
            "metadata"   : session["metadata"][idx],
            "distance"   : float(dist),       # lower = more similar
            "relevance"  : round(1 / (1 + float(dist)), 3),  # convert to 0-1 score
        })
    return results


# ─────────────────────────────────────────────
# LLM Answer Generation (the G in RAG)
# ─────────────────────────────────────────────
def generate_answer(
    question      : str,
    context_chunks: List[dict],
    chat_history  : List[dict],
) -> str:
    """
    AUGMENT the prompt with retrieved context, then GENERATE an answer.

    We build a system prompt that:
    - Tells the LLM to ONLY answer from the provided context
    - Prevents hallucination (making things up)
    - Includes the last 4 conversation turns for memory
    """
    if not groq_client:
        return (
            "⚠️ No GROQ_API_KEY set. Please add it to your .env file.\n\n"
            "Retrieved context:\n" +
            "\n---\n".join([c["text"] for c in context_chunks])
        )

    # Build context string from retrieved chunks
    context = "\n\n---\n\n".join([
        f"[Source: {c['metadata']['filename']}, chunk {c['metadata']['chunk_index']}]\n{c['text']}"
        for c in context_chunks
    ])

    system_prompt = f"""You are a helpful AI assistant that answers questions ONLY based on the provided document context.

RULES:
- Answer ONLY from the context below. Do not use outside knowledge.
- If the answer is not in the context, say "I couldn't find this information in the uploaded documents."
- Be concise and cite which document your answer comes from.
- If the question is a follow-up, use the chat history for continuity.

DOCUMENT CONTEXT:
{context}"""

    # Build messages list: system + last 4 turns of history + current question
    messages = [{"role": "system", "content": system_prompt}]
    for turn in chat_history[-4:]:            # last 4 turns = 2 questions + 2 answers
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})

    response = groq_client.chat.completions.create(
        model      = "llama-3.1-8b-instant",        # Fast, free Llama 3 8B via Groq
        messages   = messages,
        temperature= 0.2,                     # Low temperature = more factual, less creative
        max_tokens = 1024,
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "RAG Document Q&A API is running!", "docs": "/docs"}


@app.post("/session/new")
def create_session():
    """
    Creates a new chat session.
    Each session is isolated — different users get different sessions.
    Returns a session_id that the frontend stores.
    """
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "chunks"      : [],
        "metadata"    : [],
        "index"       : None,
        "chat_history": [],
        "documents"   : [],
    }
    return {"session_id": session_id}


@app.post("/upload/{session_id}")
async def upload_document(session_id: str, file: UploadFile = File(...)):
    """
    Upload a document (PDF, DOCX, TXT).

    Pipeline:
      file bytes → extract text → chunk text → embed chunks → add to FAISS index
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Create a session first.")

    allowed_types = ["application/pdf", "text/plain",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    content = await file.read()
    filename = file.filename or "unknown"

    # ── Step 1: Extract text based on file type ──
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        text = extract_text_from_pdf(content)
    elif ext == ".docx":
        text = extract_text_from_docx(content)
    elif ext == ".txt":
        text = extract_text_from_txt(content)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Use PDF, DOCX, or TXT.")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file. Is it a scanned image PDF?")

    # ── Step 2: Chunk the text ──
    new_chunks, new_meta = chunk_text(text, filename)
    print(f"  {filename}: {len(text)} chars → {len(new_chunks)} chunks")

    # ── Step 3: Add to session and rebuild FAISS index ──
    session = sessions[session_id]
    session["chunks"].extend(new_chunks)
    session["metadata"].extend(new_meta)
    session["documents"].append(filename)
    session["index"] = build_faiss_index(session["chunks"])  # rebuild with all chunks

    return {
        "message"       : f"Successfully processed '{filename}'",
        "filename"      : filename,
        "chunks_added"  : len(new_chunks),
        "total_chunks"  : len(session["chunks"]),
        "text_preview"  : text[:300] + "..."
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Main Q&A endpoint — the full RAG pipeline:
      1. Retrieve relevant chunks (semantic search)
      2. Build augmented prompt
      3. Generate answer with LLM
      4. Save to chat history
    """
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    session = sessions[req.session_id]

    if not session["chunks"]:
        raise HTTPException(status_code=400, detail="No documents uploaded yet. Please upload a document first.")

    # ── RETRIEVE ──
    relevant_chunks = retrieve_relevant_chunks(req.question, session)

    # ── GENERATE ──
    answer = generate_answer(req.question, relevant_chunks, session["chat_history"])

    # ── Save to history ──
    session["chat_history"].append({"role": "user",      "content": req.question})
    session["chat_history"].append({"role": "assistant", "content": answer})

    # Format sources for the frontend
    sources = [
        {
            "filename"    : c["metadata"]["filename"],
            "chunk_index" : c["metadata"]["chunk_index"],
            "relevance"   : c["relevance"],
            "preview"     : c["text"][:150] + "...",
        }
        for c in relevant_chunks[:3]           # show top 3 sources
    ]

    return ChatResponse(
        answer     = answer,
        sources    = sources,
        session_id = req.session_id,
    )


@app.get("/session/{session_id}", response_model=SessionInfo)
def get_session_info(session_id: str):
    """Get info about a session — useful for debugging."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    session = sessions[session_id]
    return SessionInfo(
        session_id     = session_id,
        document_count = len(session["documents"]),
        chunk_count    = len(session["chunks"]),
        chat_history   = session["chat_history"],
    )


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear all documents and chat history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    sessions[session_id] = {
        "chunks": [], "metadata": [], "index": None,
        "chat_history": [], "documents": []
    }
    return {"message": "Session cleared."}


@app.get("/health")
def health():
    return {
        "status"         : "healthy",
        "embed_model"    : EMBED_MODEL,
        "groq_connected" : groq_client is not None,
        "active_sessions": len(sessions),
    }
