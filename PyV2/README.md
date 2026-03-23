# 🌸 PCOS Chatbot with RAG + Ollama

A specialized AI chatbot for PCOS (Polycystic Ovary Syndrome) that:
- **Only answers PCOS-related questions** (filters everything else out)
- Uses **RAG (Retrieval-Augmented Generation)** for accurate, grounded answers
- Powered by **Ollama (LLaMA)** — runs fully locally, no API key needed
- Maintains **conversation history** for multi-turn dialogue

---

## 📁 File Structure

```
pcos_chatbot/
├── chatbot.py          # Main chatbot + CLI interface
├── rag_engine.py       # Embeddings, vector store, retrieval, relevance filter
├── pcos_knowledge.py   # Pre-built PCOS knowledge base (12 topics)
├── requirements.txt    # Python dependencies
└── README.md
```

---

## ⚙️ Setup

### 1. Install Ollama
```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from https://ollama.com
```

### 2. Pull Required Models
```bash
# Chat model (choose one)
ollama pull llama3.2        # Recommended (fast, good quality)
ollama pull llama3           # Alternative
ollama pull mistral          # Alternative

# Embedding model (for semantic search)
ollama pull nomic-embed-text
```

### 3. Start Ollama Server
```bash
ollama serve
```

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Chatbot
```bash
python chatbot.py
```

---

## 💬 Usage

```
╔══════════════════════════════════════════════════════╗
║          🌸  PCOS Health Assistant  🌸               ║
╚══════════════════════════════════════════════════════╝

You: What are the symptoms of PCOS?
Assistant: PCOS symptoms include irregular periods, excess androgen...

You: What's the capital of France?
Assistant: I'm a specialized PCOS health assistant, so I can only answer
          questions related to PCOS...
```

### Commands
| Command   | Description                    |
|-----------|-------------------------------|
| `/reset`  | Clear conversation history     |
| `/help`   | Show example questions         |
| `/quit`   | Exit the chatbot               |

---

## 🧠 How It Works

```
User Question
     │
     ▼
┌─────────────────────────────────┐
│   RELEVANCE GUARD (2 layers)    │
│  1. Keyword scan (fast)         │
│  2. Semantic similarity check   │
└─────────────────────────────────┘
     │
  PCOS?  ──No──► "I only answer PCOS questions"
     │
    Yes
     │
     ▼
┌─────────────────────────────────┐
│   RAG RETRIEVAL                 │
│  - Embed query                  │
│  - Search vector store          │
│  - Return top-3 relevant docs   │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│   OLLAMA (LLaMA)                │
│  Context + Question → Answer    │
└─────────────────────────────────┘
     │
     ▼
   Response to User
```

---

## 📚 Knowledge Base Topics

The pre-built knowledge base covers:
1. What is PCOS
2. Symptoms
3. Causes
4. Diagnosis (Rotterdam criteria)
5. Treatment options
6. Diet and nutrition
7. Fertility and pregnancy
8. Mental health
9. Long-term health risks
10. Exercise and lifestyle
11. PCOS in teens
12. Medications and supplements

---

## 🔧 Configuration

Edit `chatbot.py` to customize:

```python
CHAT_MODEL = "llama3.2"        # Your Ollama chat model
EMBED_MODEL = "nomic-embed-text"  # Embedding model
TOP_K_DOCS = 3                 # Docs retrieved per query
SIMILARITY_THRESHOLD = 0.25    # Relevance cutoff (0-1)
```

---

## ➕ Extending the Knowledge Base

Add more documents to `pcos_knowledge.py`:

```python
PCOS_DOCUMENTS.append({
    "id": "13",
    "topic": "Your New Topic",
    "content": "Your content here..."
})
```

Then delete `vector_cache.json` to rebuild embeddings.

---

## ⚠️ Disclaimer

This chatbot provides general health information only. It is **not a substitute for professional medical advice**. Always consult a qualified healthcare provider for diagnosis and treatment.
