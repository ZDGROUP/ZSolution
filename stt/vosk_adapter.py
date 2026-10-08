# ============================================================
#  ZSolution - Vosk STT Adapter
#  تبدیل صدا به متن با Vosk + FFmpeg
# ============================================================

import json
import os
import wave

import numpy as np
from vosk import Model as VoskModel, KaldiRecognizer, SetLogLevel

import config
from audio_utils.ffmpeg_converter import (
    convert_to_wav_16k_mono,
    ffmpeg_available,
    safe_remove,
)


class VoskSTTAdapter:
    """STT فارسی با Vosk — پشتیبانی از هر فرمت صوتی با FFmpeg."""

    def __init__(self, model_path: str = None):
        SetLogLevel(-1)
        self.model_path = model_path or config.VOSK_MODEL_PATH

        if not os.path.isdir(self.model_path):
            raise FileNotFoundError(
                f"Vosk model not found:\n  {self.model_path}"
            )

        print(f"→ Loading Vosk model from: {self.model_path}")
        self.model = VoskModel(self.model_path)
        print("→ Vosk model loaded.")

    # --------------------------------------------------------
    #  API عمومی
    # --------------------------------------------------------
    def transcribe(self, audio_path: str) -> str:
        """
        فایل صوتی با هر فرمتی (webm, ogg, wav, mp3, ...) را می‌گیرد
        و متن فارسی برمی‌گرداند.
        """
        if not audio_path or not os.path.exists(audio_path):
            print(f"  [STT] file not found: {audio_path}")
            return ""

        wav_path = None
        cleanup = False

        try:
            if ffmpeg_available():
                wav_path = convert_to_wav_16k_mono(audio_path)
                cleanup = True
            else:
                # اگر فایل WAV است، شاید مستقیم کار کند
                if audio_path.lower().endswith(".wav"):
                    wav_path = audio_path
                else:
                    raise RuntimeError(
                        "FFmpeg not available and input is not WAV."
                    )

            result = self._process_wav(wav_path)
            print(f"  [STT] {os.path.basename(audio_path)} → {result!r}")
            return result

        except Exception as e:
            print(f"  [STT] failed on {audio_path}: {e}")
            return ""

        finally:
            if cleanup:
                safe_remove(wav_path)

    # --------------------------------------------------------
    #  پردازش WAV
    # --------------------------------------------------------
    def _process_wav(self, wav_path: str) -> str:
        wf = wave.open(wav_path, "rb")

        n_channels = wf.getnchannels()
        samp_width = wf.getsampwidth()
        framerate  = wf.getframerate()

        if n_channels != 1 or samp_width != 2 or framerate != 16000:
            print(f"  [STT] WAV mismatch (ch={n_channels}, "
                  f"width={samp_width}, rate={framerate}); "
                  f"using fallback")
            return self._fallback_resample(wf)

        rec = KaldiRecognizer(self.model, 16000)
        rec.SetWords(False)

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        wf.close()

        result = json.loads(rec.FinalResult())
        return result.get("text", "").strip()

    # --------------------------------------------------------
    #  Fallback
    # --------------------------------------------------------
    def _fallback_resample(self, wf) -> str:
        n_channels = wf.getnchannels()
        framerate  = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        wf.close()

        audio = np.frombuffer(frames, dtype=np.int16)
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels)[:, 0]

        if framerate != 16000:
            n_target = int(len(audio) * 16000 / framerate)
            audio = np.interp(
                np.linspace(0, len(audio) - 1, n_target),
                np.arange(len(audio)),
                audio.astype(np.float32),
            ).astype(np.int16)

        rec = KaldiRecognizer(self.model, 16000)
        rec.SetWords(False)
        rec.AcceptWaveform(audio.tobytes())
        result = json.loads(rec.FinalResult())
        return result.get("text", "").strip()