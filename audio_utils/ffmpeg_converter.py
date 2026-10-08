# ============================================================
#  ZSolution - FFmpeg Audio Converter
#  تبدیل هر فرمت صوتی به WAV مونو 16kHz PCM 16-bit
#  الهام از VoiceAssistantServlet.java (بخش convertToWav)
# ============================================================

import os
import shutil
import subprocess
import tempfile

import config


# ============================================================
#  بررسی نصب FFmpeg
# ============================================================
def ffmpeg_available() -> bool:
    """آیا FFmpeg در PATH موجود است؟"""
    return shutil.which(config.FFMPEG_BINARY) is not None


# ============================================================
#  تبدیل به WAV 16kHz مونو
# ============================================================
def convert_to_wav_16k_mono(input_path: str) -> str:
    """
    هر فایل صوتی (WebM, OGG, MP3, M4A, WAV با هر مشخصات) را
    به WAV مونو 16kHz PCM 16-bit تبدیل می‌کند.

    Args:
        input_path: مسیر فایل ورودی

    Returns:
        مسیر فایل WAV موقت — مسئولیت پاک کردن با caller است.

    Raises:
        FileNotFoundError: اگر فایل ورودی وجود نداشته باشد.
        RuntimeError: اگر FFmpeg نبود یا تبدیل شکست بخورد.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input audio not found: {input_path}")

    if not ffmpeg_available():
        raise RuntimeError(
            "FFmpeg not found in PATH. Please install FFmpeg.\n"
            "Download: https://ffmpeg.org/download.html"
        )

    # ساخت فایل خروجی موقت
    fd, out_path = tempfile.mkstemp(suffix=".wav", prefix="zs_stt_")
    os.close(fd)

    cmd = [
        config.FFMPEG_BINARY,
        "-i", input_path,
        "-ac", "1",                 # mono
        "-ar", "16000",             # 16kHz
        "-acodec", "pcm_s16le",     # PCM 16-bit little-endian
        "-y",                       # overwrite
        out_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=config.FFMPEG_TIMEOUT,
        )
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"FFmpeg conversion failed:\n{err}")
        return out_path

    except Exception:
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except OSError:
                pass
        raise


# ============================================================
#  پاک کردن فایل موقت
# ============================================================
def safe_remove(path: str) -> None:
    """حذف امن یک فایل — خطا را نادیده می‌گیرد."""
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass