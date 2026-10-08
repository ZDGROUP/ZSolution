# ============================================================
#  ZSolution - Entry Point (FastAPI)
#  /       → Main Page (Gradio)
#  /test   → Test Page (Gradio)
#  /api/*  → FastAPI endpoints
#  /static/*, /logs/* → static
# ============================================================

import os
import uuid
import wave
import warnings
from typing import Optional

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="gradio")

import numpy as np
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import gradio as gr

import config
from stt.vosk_adapter                 import VoskSTTAdapter
from nlu.rule_based                   import RuleBasedNLU
from text2sql.mock_generator          import MockTextToSQL
from sql_guard.validator              import SQLGuard
from db.mock_adapter                  import MockDatabaseAdapter
from responder.persian_builder        import PersianResponder
from tts.pocket_tts_adapter           import PocketTTSAdapter
from core.orchestrator                import Orchestrator
from ui.gradio_app                    import build_ui
from ui.main_page                     import build_main_page


BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
LOGS_DIR   = os.path.join(BASE_DIR, "logs")
UPLOAD_DIR = os.path.join(LOGS_DIR, "uploads")
RESP_DIR   = os.path.join(LOGS_DIR, "responses")

for d in (LOGS_DIR, UPLOAD_DIR, RESP_DIR):
    os.makedirs(d, exist_ok=True)


# ============================================================
#  Orchestrator (سراسری)
# ============================================================
orch: Optional[Orchestrator] = None


def init_orchestrator():
    global orch
    print("\n[1/3] Loading modules...")
    stt       = VoskSTTAdapter(config.VOSK_MODEL_PATH)
    nlu       = RuleBasedNLU()
    text2sql  = MockTextToSQL()
    guard     = SQLGuard()
    db        = MockDatabaseAdapter()
    responder = PersianResponder()
    tts       = PocketTTSAdapter(config.TTS_MODEL_PATH,
                                 config.DEFAULT_VOICE_PATH)

    print("\n[2/3] Wiring orchestrator...")
    orch = Orchestrator(
        stt=stt,
        nlu=nlu,
        text2sql=text2sql,
        guard=guard,
        db=db,
        responder=responder,
        tts=tts,
    )


# ============================================================
#  FastAPI
# ============================================================
app = FastAPI(title="ZSolution API")


class TextRequest(BaseModel):
    text: str


def _save_response_audio(audio_chunks):
    """صدا را در فایل WAV ذخیره می‌کند و URL نسبی برمی‌گرداند."""
    try:
        parts = []
        sr = orch.tts.sample_rate
        for s, a in (audio_chunks or []):
            if a is not None:
                parts.append(a)
                sr = s
        if not parts:
            return None
        full = np.concatenate(parts)
        out_name = f"resp_{uuid.uuid4().hex[:8]}.wav"
        out_path = os.path.join(RESP_DIR, out_name)
        wf = wave.open(out_path, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(full.tobytes())
        wf.close()
        return f"/logs/responses/{out_name}"
    except Exception as e:
        print(f"[api] save audio failed: {e}")
        return None


# ------------------------------------------------------------
#  API: Voice
# ------------------------------------------------------------
@app.post("/api/voice")
async def api_voice(audio: UploadFile = File(...)):
    if orch is None:
        return JSONResponse(
            {"status": "error", "message": "orchestrator not ready"},
            status_code=503,
        )

    original_name = audio.filename or "recording.webm"
    ext = os.path.splitext(original_name)[1].lower() or ".webm"
    if ext not in (".wav", ".webm", ".ogg", ".mp3", ".m4a", ".mp4", ".opus"):
        ext = ".webm"

    in_path = os.path.join(UPLOAD_DIR, f"in_{uuid.uuid4().hex[:8]}{ext}")

    try:
        content = await audio.read()
        with open(in_path, "wb") as f:
            f.write(content)
        print(f"[api] received {len(content)} bytes "
              f"({original_name}) → {in_path}")
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": f"save failed: {e}"},
            status_code=500,
        )

    try:
        turn = orch.handle_audio(in_path)
    except Exception as e:
        print(f"[api] orchestration failed: {e}")
        return JSONResponse(
            {"status": "error",
             "message": f"orchestration failed: {e}",
             "text": "خطا در پردازش درخواست."},
            status_code=500,
        )

    audio_url = _save_response_audio(turn.audio_chunks)

    try:
        os.remove(in_path)
    except OSError:
        pass

    return {
        "status":    "success",
        "text":      turn.response_text or "",
        "audio_url": audio_url,
        "intent":    (turn.parsed_request.intent
                      if turn.parsed_request else None),
        "stt_text":  turn.recognized_text or "",
    }


# ------------------------------------------------------------
#  API: Text
# ------------------------------------------------------------
@app.post("/api/text")
async def api_text(req: TextRequest):
    if orch is None:
        return JSONResponse(
            {"status": "error", "message": "orchestrator not ready"},
            status_code=503,
        )

    text = (req.text or "").strip()
    if not text:
        return JSONResponse(
            {"status": "error", "message": "empty text"},
            status_code=400,
        )

    print(f"[api/text] received: {text!r}")

    try:
        turn = orch.handle_text(text)
    except Exception as e:
        print(f"[api/text] orchestration failed: {e}")
        return JSONResponse(
            {"status": "error",
             "message": f"orchestration failed: {e}",
             "text": "خطا در پردازش درخواست."},
            status_code=500,
        )

    audio_url = _save_response_audio(turn.audio_chunks)

    return {
        "status":    "success",
        "text":      turn.response_text or "",
        "audio_url": audio_url,
        "intent":    (turn.parsed_request.intent
                      if turn.parsed_request else None),
        "stt_text":  turn.recognized_text or "",
    }


# ------------------------------------------------------------
#  API: Health
# ------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "orchestrator": orch is not None}


# ============================================================
#  mount static & logs
# ============================================================
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/logs",   StaticFiles(directory=LOGS_DIR),   name="logs")


# ============================================================
#  Main
# ============================================================
def main():
    print("=" * 60)
    print("  ZSolution — Persian Voice Assistant")
    print("=" * 60)

    init_orchestrator()

    print("\n[3/3] Building UIs...")

    main_iface = build_main_page()
    test_iface = build_ui(orch)

    gr.mount_gradio_app(app, test_iface, path="/test")
    gr.mount_gradio_app(app, main_iface, path="/")

    print("\n" + "=" * 60)
    print(f"  Main : http://{config.SERVER_HOST}:{config.SERVER_PORT}/")
    print(f"  Test : http://{config.SERVER_HOST}:{config.SERVER_PORT}/test")
    print(f"  API  : http://{config.SERVER_HOST}:{config.SERVER_PORT}/api/voice")
    print("=" * 60 + "\n")

    uvicorn.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()