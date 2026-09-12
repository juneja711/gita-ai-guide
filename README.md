# 🕉️ Gita AI Guide ("Mayank") - Web Application

A web application bringing the timeless philosophical wisdom and ethical teachings of the **Bhagavad Gita** and **Lord Krishna** to modern life dilemmas, built with **FastAPI**, **Google Gemini**, and a serene spiritual UI.

---

## ✨ Features

- **Philosophical Lens**: Structured Gita-based counsel for modern dilemmas (Career, Anxiety, Anger, Relationships, Dharma).
- **Structured Wisdom Cards**:
  - 🌼 **Situation**: Contextual summary of the dilemma.
  - 🕉 **Krishna's Teaching**: Core philosophical lesson.
  - 📖 **Gita Principle**: Authentic chapter & verse references (e.g. Chapter 2, Verse 47).
  - 🌍 **Modern-Life Example**: Practical everyday scenario.
  - 💡 **Practical Actions**: Actionable checklist.
  - 🌿 **Reflection**: Soulful meditation thought.
- **Audio Voice Recitation**: Click the 🔊 button on any response to listen to Krishna's counsel read aloud.
- **Real-Time Streaming**: Responsive, meditative word-by-word streaming using Server-Sent Events (SSE).
- **Client & Server Key Support**: Set `GEMINI_API_KEY` on the server or allow users to supply their own free Google AI Studio key via UI settings.

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
MODEL_NAME=gemini-2.5-flash
PORT=8000
```
*(Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey))*

### 3. Start the Server
```bash
python -m uvicorn app:app --reload --port 8000
```
Open your browser and navigate to: **http://localhost:8000**

---

## 🌐 Free Cloud Deployment Options

### Option 1: Deploy on Render.com (Recommended & Free)
1. Push this folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Gita AI Guide"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/gita-ai-guide.git
   git push -u origin main
   ```
2. Log in to [Render.com](https://render.com) and click **New +** -> **Web Service**.
3. Select your GitHub repository.
4. Render will auto-detect Python, or use these settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. In the **Environment Variables** section, add:
   - `GEMINI_API_KEY` = `your_gemini_api_key`
   - `MODEL_NAME` = `gemini-2.5-flash`
6. Click **Deploy Web Service**. Your app will be live at `https://your-app-name.onrender.com` with free SSL/HTTPS!

---

### Option 2: Deploy on Railway.app
1. Go to [Railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository. Railway will detect the `Procfile` and `requirements.txt` automatically.
4. Under **Variables**, add:
   - `GEMINI_API_KEY` = `your_gemini_api_key`
5. Click **Deploy**. Railway will generate a public domain for you.

---

### Option 3: Deploy with Docker
You can run this container anywhere (AWS, Google Cloud Run, DigitalOcean, Azure):
```bash
# Build the container
docker build -t gita-ai-guide .

# Run the container
docker run -d -p 8000:8000 -e GEMINI_API_KEY="your_api_key" gita-ai-guide
```

---

## 📁 Project Structure

```
gita-ai-guide/
├── app.py                  # FastAPI server & Gemini streaming backend
├── templates/
│   └── index.html          # Responsive single-page web UI
├── static/
│   ├── css/
│   │   └── style.css       # Spiritual styling, gold accents, card animations
│   └── js/
│       └── app.js          # Chat handling, structured card parser, Web Speech
├── requirements.txt        # Python dependencies
├── Procfile                # Render / Railway process definition
├── render.yaml             # Render Blueprint specification
├── Dockerfile              # Container deployment
├── .env.example            # Environment template
└── README.md               # Documentation & deployment guide
```
