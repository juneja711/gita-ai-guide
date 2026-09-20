# 🕉️ Gita AI Guide ("Mayank") - Bhagavad Gita RAG

A spiritual AI web application bringing the timeless philosophical wisdom and ethical teachings of the **Bhagavad Gita** and **Lord Krishna** to modern life dilemmas. Built with **FastAPI**, **Google Gemini**, and a **Retrieval-Augmented Generation (RAG)** pipeline grounded in all 700 authentic Sanskrit verses across 18 chapters.

---

## ✨ Features

- **Retrieval-Augmented Generation (RAG)**:
  - **Authentic Scripture Grounding**: Every inquiry retrieves the most relevant verses from the complete 700 verses of the Bhagavad Gita.
  - **Dense Vector Search**: Powered by Google's `gemini-embedding-001` (3072-dim embeddings), precomputed in `data/gita_embeddings.npz` for sub-5ms lookups with zero startup delay.
  - **Exact Reference Parsing**: Instantly detects queries like `Chapter 2 Verse 47`, `2:47`, or `BG 18.66`.
  - **BM25 Lexical Keyword Search**: Fast sparse matching over Sanskrit transliterations, keywords, and chapter themes.
  - **Zero-Downtime Fallback**: If the embedding API is unreachable, BM25 operates 100% offline.
- **Scripture Explorer Modal**: Search any concept, dilemma, or chapter/verse reference directly from the UI.
- **Structured Wisdom Cards**:
  - 🌼 **Situation**: Contextual summary of the dilemma.
  - 🕉 **Krishna's Teaching**: Core philosophical lesson.
  - 📖 **Gita Principle**: Authentic chapter & verse references citing retrieved Shlokas.
  - 🌍 **Modern-Life Example**: Practical everyday scenario.
  - 💡 **Practical Actions**: Actionable checklist.
  - 🌿 **Reflection**: Soulful meditation thought.
- **Authentic Sanskrit Shloka Cards**:
  - Original Sanskrit text in Devanagari script.
  - Roman transliteration with accents.
  - Authentic English translation (Swami Sivananda, Shri Purohit Swami) and Hindi (Swami Ramsukhdas).
  - Match relevance score badges.
- **Audio Voice Recitation**: Listen to Krishna's counsel and translations read aloud.
- **Real-Time Streaming**: Responsive, meditative word-by-word streaming using Server-Sent Events (SSE).

---

## 🚀 Quick Start (Local)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your Google Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
MODEL_NAME=gemini-3.6-flash
PORT=8000
```
*(Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey))*

### 3. Start the Server
```bash
python -m uvicorn app:app --reload --port 8000
```
Open your browser and navigate to: **http://localhost:8000**

---

## 📡 RAG REST API Endpoints

- `POST /api/chat`: Submit life dilemma, receives SSE stream with authentic `rag` verses and response chunks.
- `GET /api/verses/search?q=karma&limit=5`: Full-text & semantic search across all 700 verses.
- `GET /api/verses/{chapter}/{verse}`: Retrieve a specific verse with Sanskrit, transliteration, English & Hindi translations.
- `GET /api/chapters`: List all 18 chapters with summary descriptions.
- `GET /api/config`: Current model, key status, and RAG index health.

---

## 🌐 Deployment (Render, Railway, Vercel, Docker)

The RAG index is lightweight (< 10MB total footprint) and runs in memory in < 15MB RAM, making it fast and deployable on any free or low-tier host:

### Option 1: Deploy on Render.com
1. Commit and push your changes to GitHub:
   ```bash
   git add .
   git commit -m "Add Bhagavad Gita RAG"
   git push origin main
   ```
2. In Render, create or open your Web Service:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `GEMINI_API_KEY`: Your Google AI Studio key
     - `MODEL_NAME`: `gemini-3.6-flash`

### Option 2: Deploy with Docker
```bash
docker build -t gita-ai-guide .
docker run -d -p 8000:8000 -e GEMINI_API_KEY="your_api_key" gita-ai-guide
```

---

## 📁 Project Structure

```
gita-ai-guide/
├── app.py                      # FastAPI server with RAG chat & search endpoints
├── rag.py                      # Core Gita RAG engine (dense vector + BM25 hybrid)
├── requirements.txt            # Python dependencies (FastAPI, NumPy, OpenAI SDK)
├── data/
│   ├── gita_verses.json        # All 701 verses with Sanskrit, translations & commentary
│   ├── chapters.json           # All 18 chapters with names and summaries
│   └── gita_embeddings.npz     # Precomputed 701-verse normalized vector index
├── scripts/
│   ├── build_gita_dataset.py   # Compiles canonical Gita JSON dataset
│   └── generate_embeddings.py  # Generates 701 dense vectors using Gemini API
├── tests/
│   └── test_rag.py             # Automated retrieval & precision tests
├── templates/
│   └── index.html              # Main spiritual UI with Scripture Explorer
├── static/
│   ├── css/style.css           # Styling, typography, Devanagari Sanskrit support
│   └── js/app.js               # Client SSE streaming & RAG cards rendering
├── public/                     # Static distribution files for serverless / CDN
│   ├── index.html
│   └── static/
└── Dockerfile
```
