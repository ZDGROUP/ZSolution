# ============================================================
#  ZSolution - Pocket TTS Adapter
#  انتقال کد فعلی TTS از zsolution_init.py به یک ماژول مستقل
# ============================================================

import os
import re
import statistics
import warnings

import numpy as np
import torch

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="gradio")

from pocket_tts import TTSModel
from transformers import AutoTokenizer, T5ForConditionalGeneration

from normalize_fa import normalize_for_model
import config


# ============================================================
#  Workaround: statistics.mean([]) raises in tts_model.py
# ============================================================
_orig_mean = statistics.mean
def _safe_mean(data, *args, **kwargs):
    if not data:
        return 0
    return _orig_mean(data, *args, **kwargs)
statistics.mean = _safe_mean


# ============================================================
#  Conjunctions & Verbs (همان کد قبلی)
# ============================================================
_CONJUNCTIONS = [
    "به شرط آنکه", "به‌شرط آنکه", "از آنجا که", "ازآنجا که",
    "از این رو", "ازاین‌رو", "با این حال", "بااین‌حال",
    "با اینکه", "بااینکه", "همین که", "همینکه",
    "زیرا که", "زیراکه", "چون که", "چونکه",
    "اگر چه", "اگرچه", "چنان که", "چنانکه",
    "چنان چه", "چنانچه", "بدان که", "بدانکه",
    "و", "یا", "پس", "اگر", "نه", "چون", "اما",
    "خواه", "زیرا", "لیکن", "ولی", "بلکه",
]
_CONJ_SORTED = sorted(_CONJUNCTIONS, key=lambda s: len(s.split()), reverse=True)

_VERB_PHRASES = [
    "شده است", "شده بود", "شده‌اند", "شده بودند",
    "نشده است", "نشده بود", "کرده است", "کرده بود",
    "کرده‌اند", "کرده بودند", "نکرده است", "نکرده بود",
    "رفته است", "رفته بود", "رفته‌اند", "رفته بودند",
    "آمده است", "آمده بود", "آمده‌اند", "داده است",
    "داده بود", "داده‌اند", "گرفته است", "گرفته بود",
    "گفته است", "گفته بود", "دیده است", "دیده بود",
    "خورده است", "خورده بود", "مانده است", "مانده بود",
    "خواسته است", "خواسته بود", "توانسته است", "توانسته بود",
]
_VERB_WORDS = {
    "است","هست","نیست","بود","نبود","باشد","نباشد",
    "هستند","نیستند","بودند","نبودند","باشند","نباشند",
    "هستم","نیستم","بودم","نبودم","باشم","نباشم",
    "هستی","نیستی","بودی","نبودی","باشی","نباشی",
    "هستیم","نیستیم","بودیم","نبودیم","باشیم","نباشیم",
    "هستید","نیستید","بودید","نبودید","باشید","نباشید",
    "شد","نشد","شده","نشده","شدم","شدی","شدیم","شدید","شدند",
    "می‌شود","نمی‌شود","می‌شوند","نمی‌شوند","می‌شد","نمی‌شد",
    "می‌شدند","نمی‌شدند","بشود","بشوند",
    "کرد","نکرد","کرده","نکرده","کردم","کردی","کردیم","کردید","کردند",
    "می‌کند","نمی‌کند","می‌کنند","نمی‌کنند","می‌کرد","نمی‌کرد",
    "می‌کردند","نمی‌کردند","بکند","بکنند",
    "داد","نداد","داده","نداده","دادم","دادی","دادیم","دادید","دادند",
    "می‌دهد","نمی‌دهد","می‌دهند","نمی‌دهند","می‌داد","نمی‌داد","بدهد","بدهند",
    "گرفت","نگرفت","گرفته","نگرفته","گرفتم","گرفتی","گرفتیم","گرفتید","گرفتند",
    "می‌گیرد","نمی‌گیرد","می‌گیرند","نمی‌گیرند","می‌گرفت","بگیرد","بگیرند",
    "رفت","نرفت","رفته","نرفته","رفتم","رفتی","رفتیم","رفتید","رفتند",
    "می‌رود","نمی‌رود","می‌روند","نمی‌روند","می‌رفت","برود","بروند",
    "آمد","نیامد","آمده","نیامده","آمدم","آمدی","آمدیم","آمدید","آمدند",
    "می‌آید","نمی‌آید","می‌آیند","نمی‌آیند","می‌آمد","بیاید","بیایند",
    "گفت","نگفت","گفته","نگفته","گفتم","گفتی","گفتیم","گفتید","گفتند",
    "می‌گوید","نمی‌گوید","می‌گویند","می‌گفت","بگوید","بگویند",
    "دید","ندید","دیده","ندیده","دیدم","دیدی","دیدیم","دیدند",
    "می‌بیند","نمی‌بیند","می‌بینند","می‌دید","ببیند","ببینند",
    "خورد","نخورد","خورده","نخورده","خوردم","خوردی","خوردند",
    "می‌خورد","نمی‌خورد","می‌خورند","بخورد","بخورند",
    "ماند","نماند","مانده","نمانده","ماندم","ماندند",
    "می‌ماند","نمی‌ماند","بماند","بمانند",
    "خواست","نخواست","خواسته","نخواسته","خواستم","خواستند",
    "می‌خواهد","نمی‌خواهد","می‌خواهند","بخواهد","بخواهند",
    "توانست","نتوانست","توانسته","نتوانسته",
    "می‌تواند","نمی‌تواند","می‌توانند","نمی‌توانند","بتواند","بتوانند",
    "رسید","نرسید","رسیده","می‌رسد","برسد",
    "افتاد","افتاده","می‌افتد","بیفتد",
    "نشست","نشسته","می‌نشیند","بنشیند",
    "ایستاد","ایستاده","می‌ایستد","بایستد",
    "برگشت","برگشته","برمی‌گردد","برگردد",
    "مرد","مرده","می‌میرد","بمیرد",
    "خرید","خریده","می‌خرد","بخرد",
    "فروخت","فروخته","می‌فروشد","بفروشد",
    "نوشت","نوشته","می‌نویسد","بنویسد",
    "خواند","خوانده","می‌خواند","بخواند",
    "شنید","شنیده","می‌شنود","بشنود",
    "دانست","دانسته","می‌داند","بداند",
    "فهمید","فهمیده","می‌فهمد","بفهمد",
}
_VERB_PHRASES_SORTED = sorted(_VERB_PHRASES, key=lambda s: len(s.split()), reverse=True)

_NO_SPLIT_BEFORE = {
    "را","به","از","با","در","بر","برای","بدون",
    "توسط","نزد","پیش","روی","زیر","بالای","کنار","بین","میان",
}

_TO_PHONEMES = str.maketrans({"/": "a", "a": "A", "@": "?", "$": "S", "c": "C"})

MIN_CONJ_SPLITS = 1
MIN_VERB_SPLITS = 1


# ============================================================
#  کلاس اصلی
# ============================================================
class PocketTTSAdapter:
    """آداپتور TTS — Pocket TTS + G2P فارسی + استریم."""

    def __init__(self, model_path: str = None, voice_path: str = None):
        model_path = model_path or config.TTS_MODEL_PATH
        voice_path = voice_path or config.DEFAULT_VOICE_PATH

        print(f"→ Loading TTS model from: {model_path}")
        self.model = TTSModel.load_model(
            config=model_path,
            temp=config.TTS_TEMPERATURE,
        )

        print(f"→ Loading default voice: {voice_path}")
        self.voice_state = self.model.get_state_for_audio_prompt(voice_path)
        self.voice_path = voice_path

        print(f"→ Loading G2P model: {config.G2P_REPO}")
        self.g2p_tok = AutoTokenizer.from_pretrained(config.G2P_REPO)
        self.g2p_model = T5ForConditionalGeneration.from_pretrained(
            config.G2P_REPO
        ).eval()

        self.sample_rate = self.model.sample_rate
        print("→ TTS adapter ready.")

    # --------------------------------------------------------
    #  تعویض صدا
    # --------------------------------------------------------
    def set_voice(self, voice_path: str):
        self.voice_state = self.model.get_state_for_audio_prompt(voice_path)
        self.voice_path = voice_path

    def reset_voice(self):
        self.voice_state = self.model.get_state_for_audio_prompt(
            config.DEFAULT_VOICE_PATH
        )
        self.voice_path = config.DEFAULT_VOICE_PATH

    # --------------------------------------------------------
    #  API عمومی: متن → generator صدا
    # --------------------------------------------------------
    def synthesize(self, text, max_chars=None, min_chars=None,
                   split_on_comma=None, rescue=None,
                   frames_after_eos=None, eos_threshold=None):
        """Generator: (sample_rate, int16_array) برمی‌گرداند."""
        max_chars         = max_chars         if max_chars         is not None else config.TTS_MAX_CHARS
        min_chars         = min_chars         if min_chars         is not None else config.TTS_MIN_CHARS
        split_on_comma    = split_on_comma    if split_on_comma    is not None else config.TTS_SPLIT_ON_COMMA
        rescue            = rescue            if rescue            is not None else config.TTS_RESCUE
        frames_after_eos  = frames_after_eos  if frames_after_eos  is not None else config.TTS_FRAMES_AFTER_EOS
        eos_threshold     = eos_threshold     if eos_threshold     is not None else config.TTS_EOS_THRESHOLD

        yield from self._synthesize_streaming(
            text, max_chars, min_chars, split_on_comma,
            rescue, frames_after_eos, eos_threshold,
        )

    def synthesize_full(self, text) -> np.ndarray:
        """همهٔ صدا را در یک آرایه برمی‌گرداند (برای تست)."""
        chunks = []
        sr = None
        for sr, audio in self.synthesize(text):
            if audio is not None:
                chunks.append(audio)
        if not chunks:
            return np.zeros(0, dtype=np.int16)
        return np.concatenate(chunks)

    # --------------------------------------------------------
    #  G2P
    # --------------------------------------------------------
    def _phonemise(self, text: str) -> str:
        text = normalize_for_model(text)
        text = text.replace("؟", "").replace("?", "")
        enc = self.g2p_tok([text], add_special_tokens=False, return_tensors="pt")
        with torch.no_grad():
            out = self.g2p_model.generate(
                **enc, num_beams=5, max_length=512, early_stopping=True
            )
        raw = self.g2p_tok.batch_decode(out, skip_special_tokens=True)[0].strip()
        return raw.replace("1", "").translate(_TO_PHONEMES)

    # --------------------------------------------------------
    #  تبدیل صدا
    # --------------------------------------------------------
    @staticmethod
    def _to_int16(audio: np.ndarray) -> np.ndarray:
        return (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)

    # --------------------------------------------------------
    #  تولید phoneme
    # --------------------------------------------------------
    def _generate_phonemes(self, phonemes, frames_after_eos):
        try:
            stream = self.model.generate_audio_stream(
                self.voice_state, phonemes, frames_after_eos=frames_after_eos
            )
        except TypeError:
            stream = self.model.generate_audio_stream(
                self.voice_state, phonemes
            )
        for frame in stream:
            arr = frame.numpy() if hasattr(frame, "numpy") else np.asarray(frame)
            yield arr.astype(np.float32).reshape(-1)

    def _stream_phonemes_faded(self, phonemes, frames_after_eos,
                               fade_len, fade_in_ramp, fade_out_ramp):
        tail = np.zeros(0, dtype=np.float32)
        fade_in_remaining = fade_len
        for frame_np in self._generate_phonemes(phonemes, frames_after_eos):
            if fade_in_remaining > 0:
                n = min(fade_in_remaining, len(frame_np))
                if n > 0:
                    start = fade_len - fade_in_remaining
                    frame_np = frame_np.copy()
                    frame_np[:n] *= fade_in_ramp[start:start + n]
                    fade_in_remaining -= n
            data = np.concatenate([tail, frame_np]) if len(tail) else frame_np
            if len(data) > fade_len:
                yield data[:-fade_len]
                tail = data[-fade_len:].copy()
            else:
                tail = data
        if len(tail) > 0:
            n = min(fade_len, len(tail))
            tail = tail.copy()
            tail[-n:] *= fade_out_ramp[-n:]
            yield tail

    # --------------------------------------------------------
    #  Streaming اصلی
    # --------------------------------------------------------
    def _synthesize_streaming(self, text, max_chars, min_chars,
                              split_on_comma, rescue,
                              frames_after_eos, eos_threshold):
        if not text or not text.strip():
            yield None
            return

        try:
            self.model.eos_threshold = float(eos_threshold)
        except Exception:
            pass

        sample_rate = self.sample_rate
        yield_every = int(sample_rate * config.TTS_YIELD_INTERVAL_SEC)
        fade_len = max(1, int(sample_rate * config.TTS_FADE_MS / 1000))
        fade_in_ramp = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        fade_out_ramp = fade_in_ramp[::-1].copy()

        sentences = self._split_sentences(text, split_on_comma)
        chunks = self._build_chunks(sentences, int(max_chars), int(min_chars))
        if not chunks:
            yield None
            return

        pending_audio = np.zeros(0, dtype=np.float32)
        samples_since_yield = 0
        buffer_text = None

        def emit(force=False):
            nonlocal pending_audio, samples_since_yield
            if force or samples_since_yield >= yield_every:
                if len(pending_audio) > 0:
                    out = (sample_rate, self._to_int16(pending_audio))
                    pending_audio = np.zeros(0, dtype=np.float32)
                    samples_since_yield = 0
                    return out
            return None

        for i, raw_text in enumerate(chunks):
            if not raw_text.strip():
                continue
            if buffer_text:
                full_text = buffer_text + " " + raw_text
                buffer_text = None
            else:
                full_text = raw_text

            try:
                phonemes = self._phonemise(full_text)
            except Exception as e:
                print(f"  ! G2P failed: {e}")
                if rescue and i + 1 < len(chunks):
                    buffer_text = full_text
                continue

            if not phonemes.strip():
                if rescue and i + 1 < len(chunks):
                    buffer_text = full_text
                continue

            try:
                for audio_part in self._stream_phonemes_faded(
                    phonemes, frames_after_eos,
                    fade_len, fade_in_ramp, fade_out_ramp,
                ):
                    pending_audio = np.concatenate([pending_audio, audio_part])
                    samples_since_yield += len(audio_part)
                    out = emit()
                    if out is not None:
                        yield out
            except Exception as e:
                print(f"  ! chunk raised {type(e).__name__}: {e}")
                if len(pending_audio) > 0:
                    yield (sample_rate, self._to_int16(pending_audio))
                    pending_audio = np.zeros(0, dtype=np.float32)
                    samples_since_yield = 0
                if rescue and i + 1 < len(chunks):
                    buffer_text = full_text
                continue

            silence = np.zeros(int(sample_rate * 0.25), dtype=np.float32)
            pending_audio = np.concatenate([pending_audio, silence])
            samples_since_yield += len(silence)
            out = emit(force=True)
            if out is not None:
                yield out

        if buffer_text and buffer_text.strip():
            try:
                phonemes = self._phonemise(buffer_text)
                if phonemes.strip():
                    for audio_part in self._stream_phonemes_faded(
                        phonemes, frames_after_eos,
                        fade_len, fade_in_ramp, fade_out_ramp,
                    ):
                        pending_audio = np.concatenate([pending_audio, audio_part])
                        samples_since_yield += len(audio_part)
                        out = emit()
                        if out is not None:
                            yield out
            except Exception:
                pass

        if len(pending_audio) > 0:
            yield (sample_rate, self._to_int16(pending_audio))

    # --------------------------------------------------------
    #  ابزارهای chunking
    # --------------------------------------------------------
    def _split_sentences(self, text, split_on_comma=True):
        text = normalize_for_model(text)
        if split_on_comma:
            text = re.sub(r'([.?!؛؟،])(\S)', r'\1 \2', text)
            sents = re.split(r'(?<=[.?!؛؟،])\s+', text)
        else:
            text = re.sub(r'([.?!؛؟])(\S)', r'\1 \2', text)
            sents = re.split(r'(?<=[.?!؛؟])\s+', text)
        return [s.strip() for s in sents if s.strip()]

    def _build_chunks(self, sentences, max_chars, min_chars):
        chunks = []
        for s in sentences:
            if len(s) <= max_chars:
                chunks.append(s); continue
            c = self._split_at_conjunctions(s, max_chars)
            if len(c) > 1:
                chunks.extend(c); continue
            chunks.extend(self._split_at_verbs(s, max_chars))
        chunks = self._merge_short(chunks, min_chars)

        enforced = []
        for c in chunks:
            c = c.strip()
            if not c:
                continue
            if len(c) <= max_chars:
                enforced.append(c)
            else:
                pieces = self._hard_split(c, max_chars)
                enforced.append(pieces[0]); enforced.extend(pieces[1:])

        return self._merge_short(enforced, min_chars)

    def _find_conj_indices(self, words):
        idxs, i = [], 0
        while i < len(words):
            for c in _CONJ_SORTED:
                cw = c.split(); n = len(cw)
                if i + n <= len(words) and all(
                    words[i + j] == cw[j] for j in range(n)
                ):
                    idxs.append(i); i += n - 1; break
            i += 1
        return idxs

    def _split_at_conjunctions(self, sentence, max_chars):
        if len(sentence) <= max_chars:
            return [sentence]
        words = sentence.split()
        idxs = self._find_conj_indices(words)
        if len(idxs) < MIN_CONJ_SPLITS:
            return [sentence]
        segs, prev = [], 0
        for idx in idxs:
            if idx <= prev: continue
            seg = " ".join(words[prev:idx]).strip()
            if seg: segs.append(seg)
            prev = idx
        tail = " ".join(words[prev:]).strip()
        if tail: segs.append(tail)
        if len(segs) <= 1: return [sentence]
        return self._pack(segs, max_chars)

    def _find_verb_end(self, words):
        ends, i = [], 0
        while i < len(words):
            ml = 0
            for ph in _VERB_PHRASES_SORTED:
                pw = ph.split(); n = len(pw)
                if i + n <= len(words) and all(
                    words[i + j] == pw[j] for j in range(n)
                ):
                    ml = n; break
            if ml == 0 and words[i] in _VERB_WORDS:
                ml = 1
            if ml > 0:
                ends.append(i + ml - 1); i += ml
            else:
                i += 1
        return ends

    def _split_at_verbs(self, sentence, max_chars):
        if len(sentence) <= max_chars:
            return [sentence]
        words = sentence.split()
        ve = self._find_verb_end(words)
        if len(ve) < MIN_VERB_SPLITS:
            return [sentence]
        sp = [idx for idx in ve if not (
            idx + 1 < len(words) and words[idx + 1] in _NO_SPLIT_BEFORE
        )]
        if not sp: return [sentence]
        segs, prev = [], 0
        for idx in sp:
            s = " ".join(words[prev:idx + 1]).strip()
            if s: segs.append(s)
            prev = idx + 1
        t = " ".join(words[prev:]).strip()
        if t: segs.append(t)
        if len(segs) <= 1: return [sentence]
        return self._pack(segs, max_chars)

    @staticmethod
    def _pack(segs, max_chars):
        chunks, cur = [], segs[0]
        for s in segs[1:]:
            if len(cur + " " + s) > max_chars and cur.strip():
                chunks.append(cur.strip()); cur = s
            else:
                cur = cur + " " + s
        if cur.strip(): chunks.append(cur.strip())
        return chunks

    @staticmethod
    def _hard_split(text, max_chars):
        words = text.split()
        if not words:
            return [text]
        pieces, cur = [], ""
        for w in words:
            if not cur:
                cur = w
            elif len(cur) + 1 + len(w) <= max_chars:
                cur = cur + " " + w
            else:
                pieces.append(cur); cur = w
        if cur:
            pieces.append(cur)
        return pieces

    @staticmethod
    def _merge_short(chunks, min_chars):
        if min_chars <= 0:
            return chunks
        merged = []
        for c in chunks:
            if merged and len(merged[-1]) < min_chars:
                merged[-1] = (merged[-1] + " " + c).strip()
            else:
                merged.append(c)
        if len(merged) >= 2 and len(merged[-1]) < min_chars:
            merged[-2] = (merged[-2] + " " + merged[-1]).strip()
            merged.pop()
        return merged