import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI(
    title="Gita AI Guide - Mayank",
    description="An AI guide bringing the timeless wisdom of the Bhagavad Gita to modern life challenges.",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prevent browser from serving stale cached JS/CSS during development
@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

SYSTEM_PROMPT = """You are an AI assistant named Mayank.
You are an AI guide whose responses are deeply inspired by the wisdom of the Bhagavad Gita and the teachings of Lord Krishna.

Your purpose is to help people navigate life's challenges by interpreting the principles of the Bhagavad Gita and applying them to modern situations.

Guidelines:

1. Answer every life-related question through the philosophical lens of the Bhagavad Gita.

2. Do not claim to literally be Lord Krishna. Instead, explain:
   - What principle from the Bhagavad Gita applies.
   - How Krishna's teachings would guide someone in this situation.
   - How those teachings can be applied in today's world.

3. Structure every response in this exact format:

━━━━━━━━━━━━━━━━━━
🌼 Situation
Briefly summarize the user's problem.

🕉 Krishna's Teaching
Explain the relevant teaching from the Bhagavad Gita in simple language.

📖 Gita Principle
Mention the relevant chapter and verse(s) when appropriate (e.g. Chapter 2, Verse 47), and summarize their meaning accurately.

🌍 Modern-Life Example
Give a practical real-world example that shows how someone can apply this teaching.

💡 Practical Actions
Provide 3–5 concrete, actionable steps the user can take.

🌿 Reflection
End with a short reflective thought inspired by the Bhagavad Gita.
━━━━━━━━━━━━━━━━━━

4. Use a compassionate, calm, and wise tone.

5. Encourage self-reflection, courage, discipline, compassion, detachment from outcomes, and ethical action.

6. Never promote hatred, violence, discrimination, or harm. If someone expresses thoughts of self-harm, harming others, or other dangerous situations, respond with empathy, encourage seeking appropriate professional support, and do not rely solely on philosophical guidance.

7. When the Bhagavad Gita does not directly address a modern issue, explain how its underlying principles can reasonably be applied without inventing teachings.

8. Be honest about uncertainty. Do not fabricate verses or claim that the Gita says something it does not.

9. Keep responses practical and easy to understand for modern readers.

Your goal is not to preach, but to help users understand how the timeless wisdom of the Bhagavad Gita can inform thoughtful decisions in everyday life."""

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    apiKey: Optional[str] = None
    model: Optional[str] = None
    stream: Optional[bool] = True

def get_openai_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if not os.path.exists(html_path):
        return HTMLResponse("<h1>Gita AI Guide is starting up...</h1>")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/config")
async def get_config():
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    return {
        "hasServerKey": bool(env_key),
        "defaultModel": os.getenv("MODEL_NAME", "gemini-3.6-flash")
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": "Gita AI Guide - Mayank",
        "version": "1.0.0"
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, authorization: Optional[str] = Header(None)):
    # Determine API key priority: request body -> Auth Header -> env variable
    api_key = (
        (request.apiKey and request.apiKey.strip())
        or (authorization and authorization.replace("Bearer ", "").strip())
        or os.getenv("GEMINI_API_KEY", "").strip()
    )

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key is required. Please set GEMINI_API_KEY in your environment/.env or provide it in the UI settings modal."
        )

    requested_model = (request.model and request.model.strip()) or os.getenv("MODEL_NAME", "gemini-3.6-flash")
    # Normalize outdated or deprecated model names from cached client state
    if requested_model in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro", ""]:
        model_name = "gemini-3.6-flash"
    else:
        model_name = requested_model

    # Build conversation messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add recent history (up to last 10 messages for context window management)
    if request.history:
        for msg in request.history[-10:]:
            if msg.role in ["user", "assistant"] and msg.content.strip():
                messages.append({"role": msg.role, "content": msg.content})

    # Add the current user message
    messages.append({"role": "user", "content": request.message})

    try:
        client = get_openai_client(api_key)

        if request.stream:
            async def event_stream():
                try:
                    try:
                        response_stream = client.chat.completions.create(
                            model=model_name,
                            messages=messages,
                            stream=True,
                            temperature=0.7
                        )
                    except Exception as first_err:
                        if model_name != "gemini-3.6-flash":
                            response_stream = client.chat.completions.create(
                                model="gemini-3.6-flash",
                                messages=messages,
                                stream=True,
                                temperature=0.7
                            )
                        else:
                            raise first_err

                    for chunk in response_stream:
                        delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else ""
                        if delta:
                            yield f"data: {json.dumps({'type': 'chunk', 'content': delta})}\n\n"
                    
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                except Exception as stream_err:
                    err_msg = str(stream_err)
                    yield f"data: {json.dumps({'type': 'error', 'error': err_msg})}\n\n"

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7
            )
            content = completion.choices[0].message.content
            return JSONResponse({"reply": content})

    except Exception as e:
        error_str = str(e)
        raise HTTPException(status_code=500, detail=f"API Error: {error_str}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
