# ============================================================
#  ZSolution - Gradio UI
#  رابط کاربری — میکروفون + متن + نمایش کامل زنجیره
# ============================================================

import os
import numpy as np
import gradio as gr

import config
from core.models import ConversationTurn


theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.indigo,
    secondary_hue=gr.themes.colors.violet,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Vazirmatn"), "Tahoma", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
)


CSS = """
:root {
    --zs-accent: #6366f1;
    --zs-accent-2: #a855f7;
    --zs-bg-1: #0f172a;
    --zs-bg-2: #1e293b;
}
.gradio-container {
    direction: rtl !important;
    text-align: right !important;
    background:
        radial-gradient(circle at 15% 10%, rgba(99,102,241,.18), transparent 45%),
        radial-gradient(circle at 85% 90%, rgba(168,85,247,.18), transparent 45%),
        linear-gradient(135deg, var(--zs-bg-1), var(--zs-bg-2)) !important;
    min-height: 100vh;
}
.gradio-container .prose,
.gradio-container label,
.gradio-container button,
.gradio-container summary,
.gradio-container .gr-check-radio label,
.gradio-container .gr-checkbox label {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
}
.gradio-container textarea,
.gradio-container input[type="text"],
.gradio-container input[type="number"],
.gradio-container input[type="search"] {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    font-size: 15px !important;
    line-height: 1.9 !important;
    background: rgba(15, 23, 42, .55) !important;
    border: 1px solid rgba(148, 163, 184, .25) !important;
    border-radius: 14px !important;
    color: #e2e8f0 !important;
    backdrop-filter: blur(12px);
}
.gradio-container input[type="range"] { direction: ltr !important; }

.zs-card {
    background: rgba(30, 41, 59, .55);
    border: 1px solid rgba(148, 163, 184, .18);
    border-radius: 20px;
    padding: 16px;
    backdrop-filter: blur(14px);
    box-shadow: 0 8px 24px rgba(0,0,0,.25);
}

#gen-btn {
    background: linear-gradient(135deg, var(--zs-accent), var(--zs-accent-2)) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 16px !important;
    padding: 16px 22px !important;
    font-size: 18px !important;
    letter-spacing: .3px;
    box-shadow: 0 8px 24px rgba(99,102,241,.45) !important;
    transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
    width: 100%;
}
#gen-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(99,102,241,.65) !important;
    filter: brightness(1.05);
}

.gradio-container details > summary {
    font-weight: 600 !important;
    padding: 12px 16px !important;
    border-radius: 14px !important;
    background: rgba(99, 102, 241, .12) !important;
    border: 1px solid rgba(148, 163, 184, .15) !important;
    cursor: pointer;
    color: #cbd5e1 !important;
    margin-bottom: 6px !important;
}

#out-audio {
    min-height: 120px !important;
    max-height: 200px !important;
    overflow: hidden !important;
    border-radius: 18px !important;
    background: rgba(15, 23, 42, .5) !important;
    border: 1px solid rgba(148, 163, 184, .2) !important;
}
#out-audio svg { max-height: 64px !important; max-width: 64px !important; }

.gradio-container h1 {
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #a5b4fc, #e9d5ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 30px !important;
    margin-bottom: 4px !important;
}
"""


# ============================================================
#  helpers
# ============================================================
def _collect_audio(chunks) -> tuple:
    """generator صدا را در یک آرایه جمع می‌کند."""
    if chunks is None:
        return None
    try:
        sr = None
        parts = []
        for sr, audio in chunks:
            if audio is not None:
                parts.append(audio)
        if not parts:
            return None
        return (sr, np.concatenate(parts))
    except Exception as e:
        print(f"! collect audio failed: {e}")
        return None


def _empty_outputs():
    return (
        "(هیچ ورودی‌ای داده نشد)",   # recognized
        "—",                          # intent
        "—",                          # entities
        "—",                          # sql
        "—",                          # db status
        "—",                          # response
        None,                         # audio
    )


def _turn_to_outputs(turn: ConversationTurn):
    """ConversationTurn → tuple خروجی‌های UI."""
    recognized = turn.recognized_text or "—"

    if turn.parsed_request:
        intent = turn.parsed_request.intent
        entities = (
            str(turn.parsed_request.entities)
            if turn.parsed_request.entities else "—"
        )
    else:
        intent = "—"
        entities = "—"

    if turn.sql_query and turn.sql_query.valid:
        sql = turn.sql_query.sql
    else:
        sql = "—"

    if turn.query_result:
        db_status = (
            f"status={turn.query_result.status}  "
            f"rows={turn.query_result.row_count}  "
            f"{'(mock)' if turn.query_result.is_mock else ''}"
        )
    else:
        db_status = "—"

    response = turn.response_text or "—"

    audio = _collect_audio(turn.audio_chunks)

    return (recognized, intent, entities, sql, db_status, response, audio)


# ============================================================
#  handlers
# ============================================================
def on_audio(orch, audio_path):
    if not audio_path:
        return _empty_outputs()
    try:
        turn = orch.handle_audio(audio_path)
    except Exception as e:
        return _empty_outputs()[:5] + (f"❌ خطا: {e}", None)
    return _turn_to_outputs(turn)


def on_text(orch, text):
    if not text or not text.strip():
        return _empty_outputs()
    try:
        turn = orch.handle_text(text)
    except Exception as e:
        return _empty_outputs()[:5] + (f"❌ خطا: {e}", None)
    return _turn_to_outputs(turn)


def set_voice(orch, voice_file):
    if voice_file is None:
        return "ℹ️ فایلی انتخاب نشده."
    try:
        orch.tts.set_voice(voice_file)
        return f"✅ صدای جدید بارگذاری شد: `{os.path.basename(voice_file)}`"
    except Exception as e:
        return f"❌ خطا: {e}"


def reset_voice(orch):
    try:
        orch.tts.reset_voice()
        return "✅ بازگشت به صدای پیش‌فرض."
    except Exception as e:
        return f"❌ خطا: {e}"


# ============================================================
#  UI Builder
# ============================================================
def build_ui(orch):

    with gr.Blocks(
        title="ZSolution — دستیار صوتی فارسی",
        theme=theme,
        css=CSS,
    ) as iface:

        gr.HTML("""
        <div style="text-align:center; margin-bottom:10px;">
            <h1>🎙️ دستیار صوتی هوشمند فارسی</h1>
            <p style="color:#94a3b8;font-size:14px;margin-top:0;">
            صحبت کن یا بنویس — سیستم intent را تشخیص می‌دهد،
            SQL می‌سازد، از دیتابیس Mock می‌خواند و پاسخ صوتی می‌دهد.
            </p>
        </div>
        """)

        with gr.Row():

            # ------------- ستون چپ: ورودی -------------
            with gr.Column(scale=5):

                gr.Markdown("### 🎤 ورودی صوتی")
                mic_in = gr.Audio(
                    label="کلیک کنید و صحبت کنید (برای توقف دوباره کلیک کنید)",
                    sources=["microphone", "upload"],
                    type="filepath",
                )
                btn_audio = gr.Button(
                    "🎧 پردازش صدا",
                    variant="primary",
                    elem_id="gen-btn",
                )

                gr.Markdown("### ⌨️ یا ورودی متنی")
                txt_in = gr.Textbox(
                    label="",
                    placeholder="مثلاً: موجودی ورق فولادی در انبار مرکزی چقدر است؟",
                    lines=3,
                    rtl=True,
                    show_label=False,
                )
                btn_text = gr.Button(
                    "📨 پردازش متن",
                    variant="secondary",
                )

                with gr.Accordion("🎚️ تنظیمات صدا", open=False):
                    opt_voice = gr.Audio(
                        label="فایل صدای مرجع (≤۵ ثانیه)",
                        sources=["upload"],
                        type="filepath",
                    )
                    voice_status = gr.Markdown(
                        "ℹ️ صدای پیش‌فرض فعال است."
                    )
                    with gr.Row():
                        btn_voice_set   = gr.Button("بارگذاری صدا", size="sm")
                        btn_voice_reset = gr.Button("پیش‌فرض", size="sm")

            # ------------- ستون راست: خروجی -------------
            with gr.Column(scale=5):

                gr.Markdown("### 🔊 پاسخ صوتی")
                out_audio = gr.Audio(
                    label="",
                    type="numpy",
                    autoplay=True,
                    elem_id="out-audio",
                    show_label=False,
                )

                gr.Markdown("### 💬 پاسخ متنی")
                out_response = gr.Textbox(
                    label="",
                    lines=2,
                    rtl=True,
                    interactive=False,
                    show_label=False,
                )

                with gr.Accordion("🔍 جزئیات فنی (برای توسعه‌دهنده)", open=False):
                    out_recognized = gr.Textbox(
                        label="متن شناسایی‌شده (STT)",
                        rtl=True, interactive=False,
                    )
                    out_intent = gr.Textbox(
                        label="Intent تشخیص‌داده‌شده",
                        interactive=False,
                    )
                    out_entities = gr.Textbox(
                        label="Entities",
                        interactive=False,
                    )
                    out_sql = gr.Code(
                        label="SQL تولیدشده (Mock)",
                        language="sql",
                    )
                    out_db = gr.Textbox(
                        label="وضعیت دیتابیس",
                        interactive=False,
                    )

        # ---------------- رویدادها ----------------
        btn_voice_set.click(
            fn=lambda v: set_voice(orch, v),
            inputs=opt_voice, outputs=voice_status,
        )
        btn_voice_reset.click(
            fn=lambda: reset_voice(orch),
            inputs=None, outputs=voice_status,
        )

        outputs = [out_recognized, out_intent, out_entities,
                   out_sql, out_db, out_response, out_audio]

        btn_audio.click(
            fn=lambda p: on_audio(orch, p),
            inputs=mic_in,
            outputs=outputs,
        )
        btn_text.click(
            fn=lambda t: on_text(orch, t),
            inputs=txt_in,
            outputs=outputs,
        )

    return iface