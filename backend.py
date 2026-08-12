"""
backend.py

FastAPI + Celery backend with server-side Marathi translation for AI outputs.
- POST /start_conversation -> enqueue Celery task
- GET /task/{task_id} -> check status/result
- GET /events/{task_id} -> SSE progress stream

Run:
  docker-compose (provided) or run Redis + Celery worker + uvicorn
"""
import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, BaseSettings, root_validator, validator
from sse_starlette.sse import EventSourceResponse

from celery import Celery, states
from celery.result import AsyncResult

import httpx

# Optional GenAI imports
try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

# Optional googletrans fallback
try:
    from googletrans import Translator
except Exception:
    Translator = None

# ---------- Settings ----------
class Settings(BaseSettings):
    REDIS_URL: str = Field("redis://localhost:6379/0")
    CELERY_QUEUE: str = Field("vsp1_tasks")
    GEMINI_API_KEY: Optional[str] = Field(None)
    TRANSLATE_API_KEY: Optional[str] = Field(None)
    ALLOWED_ORIGINS: str = Field("http://localhost:8501")
    MAX_PROMPT_LENGTH: int = 1600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
ALLOWED_ORIGINS = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vsp1-backend")

# ---------- Celery ----------
celery_app = Celery("vsp1", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_default_queue = settings.CELERY_QUEUE
celery_app.conf.task_routes = {"backend.run_conversation": {"queue": settings.CELERY_QUEUE}}
celery_app.conf.worker_max_tasks_per_child = 100

# ---------- Pydantic guardrails ----------
class ConversationRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    user_message: str = Field(..., min_length=1, max_length=settings.MAX_PROMPT_LENGTH)
    ui_language: Optional[str] = Field("en", description="ISO code: en, mr, etc.")

    @root_validator
    def forbid_hallucination_phrases(cls, values):
        msg = (values.get("user_message") or "").lower()
        forbidden = ["invent", "make up", "hallucinate", "fabricate", "guess"]
        for p in forbidden:
            if p in msg:
                raise ValueError(f"Prompt contains forbidden phrase: {p}")
        return values


class AIOutputSchema(BaseModel):
    summary: str = Field(..., description="Concise factual summary", max_length=6000)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence [0..1]")
    evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    language: Optional[str] = Field("en")

    @validator("summary")
    def ensure_non_speculative(cls, v):
        low = v.lower()
        disallowed = ["definitely", "100% certain", "guarantee", "without doubt"]
        for ph in disallowed:
            if ph in low:
                raise ValueError("Summary appears overconfident/speculative")
        return v


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

# ---------- Helpers ----------
async def fetch_weather(lat: float, lon: float) -> Dict[str, Any]:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()

async def fetch_elevation(lat: float, lon: float) -> Dict[str, Any]:
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()


def call_gemini_sync(prompt: str, context: Dict[str, Any]) -> str:
    """
    Synchronous wrapper: calls GenAI via google-genai SDK if available and key present.
    Raises RuntimeError if not configured or call fails.
    """
    if not settings.GEMINI_API_KEY or genai is None:
        raise RuntimeError("Gemini not configured on backend")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    system_instruction = (
        "You are VSP-1, a global geological intelligence assistant. "
        "Return EXACTLY one JSON object with fields: summary, confidence, evidence, language. "
        "Summary must be factual, concise, and explicitly state uncertainty. No hallucinations."
    )
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f"Context: {json.dumps(context)}\n\nUser: {prompt}",
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.15),
        )
        if hasattr(response, "text") and response.text:
            return response.text
        try:
            return str(response.output[0].content[0].text)
        except Exception:
            return str(response)
    except Exception as e:
        raise RuntimeError(f"Gemini call failed: {e}")


# Translation helper (server-side)
def translate_text_to_target(text: str, target_lang: str = "mr") -> str:
    """
    Translate `text` to `target_lang`.
    1) If TRANSLATE_API_KEY is set, call Google Cloud Translate v2 REST API.
    2) Else try googletrans (if installed).
    3) Else return original text.
    """
    if not text:
        return text

    api_key = settings.TRANSLATE_API_KEY
    # 1) Google Cloud Translate API (v2)
    if api_key:
        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            payload = {"q": text, "target": target_lang, "format": "text", "key": api_key}
            resp = httpx.post(url, data=payload, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            return data["data"]["translations"][0]["translatedText"]
        except Exception:
            logging.exception("Translate API failed; falling back")
    # 2) googletrans fallback
    if Translator is not None:
        try:
            translator = Translator()
            res = translator.translate(text, dest=target_lang)
            return res.text
        except Exception:
            logging.exception("googletrans translate failed")
    # 3) fallback: return original
    return text


# ---------- Celery Task ----------
@celery_app.task(bind=True)
def run_conversation(self, lat: float, lon: float, user_message: str, ui_language: str = "en") -> Dict[str, Any]:
    """
    Durable Celery task: fetch geo data, call AI (if available), validate output schema.
    Uses update_state to provide progress meta for SSE/polling.
    """
    try:
        self.update_state(state="RUNNING", meta={"progress": 5})
        # Step 1: fetch weather & elevation
        try:
            weather = httpx.get(
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true",
                timeout=8,
            ).json()
        except Exception as e:
            weather = {"error": f"weather fetch failed: {e}"}
        self.update_state(state="RUNNING", meta={"progress": 30})

        try:
            elevation = httpx.get(f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}", timeout=8).json()
        except Exception as e:
            elevation = {"error": f"elevation fetch failed: {e}"}
        self.update_state(state="RUNNING", meta={"progress": 60})

        # Step 2: try call Gemini
        ai_output_valid = None
        ai_used_gemini = False
        try:
            ai_raw = call_gemini_sync(user_message, {"weather": weather, "elevation": elevation, "coords": {"lat": lat, "lon": lon}})
            parsed = json.loads(ai_raw)
            ai_output_valid = AIOutputSchema.parse_obj(parsed)
            ai_used_gemini = True
            self.update_state(state="RUNNING", meta={"progress": 90, "ai_valid": True})
        except Exception as e:
            logger.warning("Gemini failed or output invalid: %s", e)
            ai_output_valid = AIOutputSchema(
                summary=(
                    "AGI unavailable or returned unexpected format. Deterministic summary: "
                    f"weather_available={('error' not in weather)}, elevation_available={('error' not in elevation)}."
                ),
                confidence=0.35,
                evidence={"weather": weather if "error" not in weather else {}, "elevation": elevation if "error" not in elevation else {}},
                language="en",
            )
            self.update_state(state="RUNNING", meta={"progress": 85, "ai_valid": False, "ai_error": str(e)})

        # Server-side translation to Marathi
        try:
            translated_summary = translate_text_to_target(ai_output_valid.summary, target_lang="mr")
            ai_localized = {
                "summary": translated_summary,
                "confidence": max(min(ai_output_valid.confidence * 0.95, 1.0), 0.0),
                "language": "mr",
                "evidence": ai_output_valid.evidence,
            }
        except Exception as e:
            logging.exception("Translation failed")
            ai_localized = {"summary": ai_output_valid.summary, "confidence": ai_output_valid.confidence, "language": ai_output_valid.language, "evidence": ai_output_valid.evidence}

        final = {
            "weather": weather,
            "elevation": elevation,
            "ai": ai_output_valid.dict(),
            "ai_localized": ai_localized,
            "meta": {"used_gemini": ai_used_gemini},
        }

        self.update_state(state="SUCCESS", meta={"progress": 100, "result": final})
        return final
    except Exception as exc:
        logging.exception("Task run_conversation failed: %s", exc)
        self.update_state(state=states.FAILURE, meta={"error": str(exc)})
        raise


# ---------- FastAPI app ----------
app = FastAPI(title="VSP-1 Geological Intelligence (backend)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/start_conversation")
async def start_conversation(req: ConversationRequest):
    try:
        async_result = run_conversation.apply_async(args=[req.lat, req.lon, req.user_message, req.ui_language])
        return {"task_id": async_result.id, "status": "PENDING", "queued_at": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.exception("Failed to start conversation: %s", e)
        raise HTTPException(status_code=500, detail="Failed to enqueue task")

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    try:
        res = AsyncResult(task_id, app=celery_app)
        meta = res.info or {}
        status = res.status
        progress = int(meta.get("progress") or (100 if status in ("SUCCESS", "FAILURE") else 0))
        result = meta.get("result") if isinstance(meta.get("result"), dict) else None
        error = meta.get("error")
        return TaskStatusResponse(
            task_id=task_id,
            status=status,
            progress=progress,
            result=result,
            error=error,
            started_at=None,
            finished_at=None,
        ).dict()
    except Exception as e:
        logger.exception("Failed to fetch task status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch task status")

@app.get("/events/{task_id}")
async def events(request: Request, task_id: str):
    async def generator():
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected: %s", task_id)
                    break
                res = AsyncResult(task_id, app=celery_app)
                meta = res.info or {}
                status = res.status
                progress = int(meta.get("progress") or (100 if status in ("SUCCESS", "FAILURE") else 0))
                payload = {"task_id": task_id, "status": status, "progress": progress, "meta": meta}
                yield {"event": "progress", "data": json.dumps(payload)}
                if status in ("SUCCESS", "FAILURE"):
                    break
                await asyncio.sleep(1.0)
        except Exception as e:
            logger.exception("SSE generator error: %s", e)
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(generator())

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
