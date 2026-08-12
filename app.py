"""
Updated Streamlit frontend (app.py)

- Expects backend to return both original AI output and server-side Marathi translation.
- Displays English summary and Marathi summary if available.
- Uses @st.cache_data for elevation caching.
- Non-blocking SSE/polling is preserved (SSE optional).
"""
import os
import time
import threading
import json
from typing import Optional

import requests
import streamlit as st
from pydantic import BaseModel, Field, ValidationError

# Optional SSE client for streaming events
try:
    from sseclient import SSEClient
except Exception:
    SSEClient = None

BACKEND_URL = os.environ.get("STREAMLIT_BACKEND_URL", "http://localhost:8000")

# Simple i18n: added Marathi ('mr') display labels
I18N = {
    "en": {
        "title": "VSP-1 Geological Intelligence — Global Chat",
        "input_placeholder": "Ask a geological question (e.g., bearing capacity, risk assessment)...",
        "start": "Send",
        "starting_analysis": "Starting analysis...",
        "no_backend": "Backend unreachable; try local quick summary.",
        "local_summary": "Quick local summary",
    },
    "mr": {
        "title": "VSP-1 भूगर्भीय बुद्धिमत्ता — ग्लोबल चॅट",
        "input_placeholder": "भू-वैज्ञानिक प्रश्न विचारा...",
        "start": "पाठवा",
        "starting_analysis": "विश्लेषण सुरू केले जात आहे...",
        "no_backend": "बॅकएंड उपलब्ध नाही; स्थानिक संक्षेप वापरून पहा.",
        "local_summary": "त्वरीत स्थानिक सारांश",
    },
}

# Client-side guardrails
class ClientGuardrails(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    message: str = Field(..., min_length=1, max_length=1600)

    @staticmethod
    def check_forbidden(message: str):
        forbidden = ["invent", "make up", "hallucinate", "fabricate", "guess"]
        low = message.lower()
        for p in forbidden:
            if p in low:
                raise ValueError("Message contains forbidden phrasing; please reword.")

# Cached geospatial call
@st.cache_data(ttl=60 * 60)
def cached_elevation(lat: float, lon: float) -> dict:
    try:
        r = requests.get(f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}", timeout=6)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": f"Elevation fetch failed: {e}"}

# Backend helpers
def start_backend_conversation(lat: float, lon: float, message: str, ui_language: str) -> Optional[str]:
    payload = {"lat": lat, "lon": lon, "user_message": message, "ui_language": ui_language}
    try:
        r = requests.post(f"{BACKEND_URL}/start_conversation", json=payload, timeout=10)
        r.raise_for_status()
        return r.json().get("task_id")
    except Exception as e:
        st.error(f"Failed to reach backend: {e}")
        return None

def fetch_task_once(task_id: str) -> dict:
    try:
        r = requests.get(f"{BACKEND_URL}/task/{task_id}", timeout=6)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# SSE listener
def sse_poll(task_id: str):
    st.session_state[f"sse_active_{task_id}"] = True
    url = f"{BACKEND_URL}/events/{task_id}"
    try:
        if SSEClient is None:
            raise RuntimeError("sseclient not installed")
        messages = SSEClient(url, retry=3000)
        for msg in messages:
            if msg.event == "progress":
                try:
                    payload = json.loads(msg.data)
                except Exception:
                    payload = {"error": "invalid json in sse"}
                st.session_state["task_status"] = payload.get("status")
                st.session_state["task_progress"] = int(payload.get("progress") or 0)
                meta = payload.get("meta", {})
                if meta.get("result"):
                    st.session_state["task_result"] = meta.get("result")
                if payload.get("status") in ("SUCCESS", "FAILURE"):
                    break
            elif msg.event == "error":
                st.session_state["last_error"] = msg.data
                break
    except Exception as e:
        st.session_state["sse_error"] = str(e)
    finally:
        st.session_state[f"sse_active_{task_id}"] = False

# Polling fallback
def polling_fallback(task_id: str, interval: float = 2.0):
    st.session_state[f"poll_active_{task_id}"] = True
    while True:
        status = fetch_task_once(task_id)
        if "error" in status and status.get("status") is None:
            st.session_state["last_error"] = status.get("error")
            break
        st.session_state["task_status"] = status.get("status")
        st.session_state["task_progress"] = int(status.get("progress") or 0)
        if status.get("result"):
            st.session_state["task_result"] = status.get("result")
        if status.get("status") in ("SUCCESS", "FAILURE"):
            break
        time.sleep(interval)
    st.session_state[f"poll_active_{task_id}"] = False

# Streamlit UI
st.set_page_config(page_title="VSP-1 Chat UI", page_icon="🛰️", layout="wide")
lang = st.sidebar.selectbox("UI Language", options=["en", "mr"], index=0)
labels = I18N.get(lang, I18N["en"])

st.markdown(f"## {labels['title']}")
st.write("Enterprise-grade geological chat with real-time analysis & international UI.")

left_col, right_col = st.columns([3, 1])

# Initialize session_state
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "text": "You are VSP-1: provide concise, factual geotechnical answers. If uncertain, say so.", "ts": time.time()}
    ]
for k in ("task_status", "task_progress", "task_result", "current_task_id", "last_error", "sse_error"):
    if k not in st.session_state:
        st.session_state[k] = None

with right_col:
    st.markdown("### Controls")
    lat = st.number_input("Latitude", value=18.5204, format="%.6f")
    lon = st.number_input("Longitude", value=73.8567, format="%.6f")
    ui_lang = st.selectbox("Response language", options=["en", "mr"], index=0)
    st.markdown("---")
    with st.expander("Elevation"):
        elev = cached_elevation(lat, lon)
        st.json(elev)
    st.markdown("---")
    if st.button(labels["local_summary"]):
        try:
            elev = cached_elevation(lat, lon)
            local = {
                "coords": {"lat": lat, "lon": lon},
                "elevation": elev,
                "note": "Local fallback summary. For deeper, use backend analysis.",
            }
            st.json(local)
        except Exception as e:
            st.error(f"Local summary failed: {e}")

with left_col:
    st.markdown("### Conversation")
    for msg in st.session_state["messages"]:
        role = msg["role"]
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg["ts"]))
        if role == "system":
            st.info(f"[system] {msg['text']}\n\n*{ts}*")
        elif role == "user":
            st.markdown(f"**You** — {ts}\n\n{msg['text']}")
        else:
            st.success(f"**VSP-1** — {ts}\n\n{msg['text']}")

    st.markdown("---")
    placeholder = st.empty()
    with placeholder.form(key="message_form", clear_on_submit=True):
        user_input = st.text_area("Message", placeholder=labels["input_placeholder"], height=120)
        submitted = st.form_submit_button(labels["start"])

    if submitted and user_input and user_input.strip():
        try:
            guard = ClientGuardrails(lat=lat, lon=lon, message=user_input)
            ClientGuardrails.check_forbidden(user_input)
        except ValidationError as ve:
            st.error(f"Validation error: {ve}")
        except ValueError as ve:
            st.error(f"Guardrail rejection: {ve}")
        else:
            st.session_state["messages"].append({"role": "user", "text": user_input, "ts": time.time()})
            with st.spinner(labels["starting_analysis"]):
                task_id = start_backend_conversation(lat, lon, user_input, ui_lang)
                if not task_id:
                    st.warning(labels["no_backend"])
                else:
                    st.session_state["current_task_id"] = task_id
                    st.session_state["task_status"] = "PENDING"
                    st.session_state["task_progress"] = 0
                    st.session_state["task_result"] = None
                    st.session_state["last_error"] = None
                    st.session_state["sse_error"] = None

                    if SSEClient is not None:
                        t = threading.Thread(target=sse_poll, args=(task_id,), daemon=True)
                        t.start()
                    else:
                        t = threading.Thread(target=polling_fallback, args=(task_id,), daemon=True)
                        t.start()

    st.markdown("### Analysis status")
    st.write(f"Status: {st.session_state.get('task_status') or 'idle'}")
    try:
        st.progress(min(max(int(st.session_state.get("task_progress") or 0), 0), 100))
    except Exception:
        st.text(f"Progress: {st.session_state.get('task_progress')}")
    if st.session_state.get("last_error"):
        st.error(st.session_state.get("last_error"))
    if st.session_state.get("sse_error"):
        st.warning(f"SSE error: {st.session_state.get('sse_error')} — falling back to polling")

    # Show result: expect backend to return ai (original) and ai_localized (mr)
    if st.session_state.get("task_result"):
        res = st.session_state["task_result"]
        st.markdown("### Result (validated by backend)")
        st.json(res)
        ai = res.get("ai") if isinstance(res, dict) else None
        ai_local = res.get("ai_localized") if isinstance(res, dict) else None

        if ai:
            st.markdown("#### AI Summary (Original)")
            st.write(ai.get("summary"))
            st.caption(f"Confidence: {ai.get('confidence')}")
            # Append to chat history
            st.session_state["messages"].append({"role": "assistant", "text": ai.get("summary", ""), "ts": time.time()})

        if ai_local and ai_local.get("language") == "mr":
            st.markdown("#### AI Summary (Marathi)")
            st.write(ai_local.get("summary"))
            st.caption("Localized (Marathi) — translated on backend")

st.markdown("---")
st.caption(f"Backend: {BACKEND_URL} — SSE support: {'yes' if SSEClient is not None else 'no'}")
