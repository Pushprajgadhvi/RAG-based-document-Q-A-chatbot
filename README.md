# 📚 RAG-Based Document Q&A Chatbot

An AI-powered chatbot that lets you **upload documents (PDFs)** and **ask questions about their content** using Retrieval-Augmented Generation (RAG). The system retrieves the most relevant chunks from your document and uses an LLM (via **Groq**) to generate accurate, context-aware answers.

## 🚀 Live Demo

### 👉 [**Click here to try the live app**](https://frontend-eight-rust-31.vercel.app/)

Upload a PDF and start asking questions instantly — no setup required.

---

## ✨ Features

- 📄 Upload PDF documents and automatically process them into chunks
- 🔍 Semantic retrieval of relevant document chunks based on your question
- 🤖 LLM-powered answers (via Groq API) grounded in your document's content
- ⚡ Fast responses powered by Groq's high-speed inference
- 🌐 Full-stack deployment — frontend and backend hosted separately for scalability

---

## 🛠️ Tech Stack

| Layer        | Technology                          |
|--------------|--------------------------------------|
| Frontend     | React / Next.js, deployed on **Vercel** |
| Backend      | FastAPI (Python), deployed on **Hugging Face Spaces** |
| LLM Provider | **Groq API** |
| Server       | Uvicorn |

---

## 📂 Project Structure

```
rag-chatbot/
├── backend/
│   ├── main.py            # FastAPI app entry point
│   ├── requirements.txt   # Backend dependencies
│   └── ...
├── frontend/
│   ├── src/                # Frontend source code
│   ├── package.json
│   └── ...
└── README.md
```

---

## ⚙️ How It Works

1. **Upload** a PDF document through the web interface
2. The backend **splits the document into chunks** and creates embeddings
3. When you ask a question, the system **retrieves the most relevant chunks**
4. The retrieved context + your question is sent to **Groq's LLM**
5. The chatbot returns an **answer grounded in your document**

---

## 🔧 Local Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the backend folder:
```
GROQ_API_KEY=your_groq_api_key_here
```

Run the server:
```bash
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🌍 Deployment

- **Frontend** → Deployed on [Vercel](https://vercel.com)
- **Backend** → Deployed on [Hugging Face Spaces](https://huggingface.co/spaces)


---

## 📌 Future Improvements

- [ ] Support for multiple document uploads at once
- [ ] Display source chunks/citations alongside answers
- [ ] Support for more file types (DOCX, TXT)
- [ ] Chat history persistence

---

## 👤 Author

**Pushpraj Gadhvi**
[GitHub](https://github.com/Pushprajgadhvi)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
