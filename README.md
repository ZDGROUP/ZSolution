# 🎙️ ZAI Assistant

**Offline Persian Speech-to-Speech AI Assistant with NLU, Text-to-SQL, and streaming TTS**

A fully offline voice assistant that understands spoken Persian requests, translates them to SQL, executes them on a local database, and replies with natural voice — no cloud APIs, no internet connection required.

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Why Offline?](#-why-offline)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Model Setup](#-model-setup)
- [Running the App](#-running-the-app)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Data Contracts](#-data-contracts)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🎯 Overview

**ZAI Assistant** is a Persian (Farsi) voice assistant built entirely with open-source, offline-first tools. It receives spoken input, converts it to text, understands the user's intent, generates a valid SQL query, executes it against a local database, and speaks back the answer — all without a network connection.

### Example Interaction

> **User speaks:** «موجودی ورق فولادی در انبار مرکزی چقدر است؟»
> *("What is the current stock of steel sheets in the central warehouse?")*
>
> **ZAI responds:** «موجودی ورق فولادی در انبار مرکزی برابر ۱۲۰۰ کیلوگرم است.»
> *("The stock of steel sheets in the central warehouse is 1200 kilograms.")*
>
> *(The response is played as natural voice simultaneously)*

---

## ✨ Key Features

- 🎤 **Automatic Speech Recognition** — Persian STT using Vosk
- 🔊 **Natural Speech Synthesis** — Persian TTS using Pocket TTS
- 🧠 **Intent Recognition** — Rule-based NLU for common queries
- 🔄 **Text-to-SQL Pipeline** — Converts natural language to valid SQL
- 🛡️ **SQL Guard** — Validates and sanitizes all queries before execution
- 💾 **Mock Database** — Predefined schema and data for testing
- 🌐 **Modern Web UI** — Two-column layout with real-time history
- ⌨️ **Dual Input** — Voice or text input
- 🎨 **Fluent Design** — Clean, modern interface inspired by Dynamics 365
- 🎬 **Voice Activity Detection (VAD)** — Auto-detects when the user stops speaking
- 🔒 **100% Offline** — No cloud APIs, no internet, no external services

---

## 🔒 Why Offline?

Running fully offline provides significant advantages:

| Advantage | Benefit |
|-----------|---------|
| **No Cloud APIs** | Zero requests to external servers |
| **Data Privacy** | Voice and text never leave the machine |
| **Lower Latency** | No network round-trip delays |
| **No API Costs** | Free forever, no usage limits |
| **Works Anywhere** | Usable in air-gapped or restricted environments |
| **No Rate Limits** | Unlimited requests |
| **Full Control** | Complete transparency over data processing |

**Note:** An internet connection is only needed **once** to download the models. After that, the application runs completely offline.

---

## 🏗️ Architecture

┌──────────────────────────────────────────────────────────────┐
│ Web UI (Gradio) │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Main Page (/) — Auto VAD + Auto Playback │ │
│ │ Test Page (/test) — Manual input form │ │
│ └────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ Orchestrator — Conversation Flow │
└──┬────┬──────┬──────┬──────┬───────┬───────┬────────────────┘
│ │ │ │ │ │ │
▼ ▼ ▼ ▼ ▼ ▼ ▼
┌────┐┌────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐
│STT ││NLU ││Text2 ││SQL ││Mock ││Persian││TTS │
│Vosk││Rule││SQL ││Guard ││DB ││Resp. ││Pocket│
│+FF ││Base││Mock ││Valid ││Adapt ││Build ││+G2P │
└────┘└────┘└──────┘└──────┘└──────┘└──────┘└──────┘
text


### Design Principles

1. **Separation of Concerns** — Each module has one responsibility
2. **Explicit Contracts** — All modules communicate via `dataclass`
3. **UI-Independent Logic** — Business logic lives in `core/`, UI is display only
4. **Replaceable Components** — Any module can be swapped without touching others
5. **Security by Default** — SELECT-only queries, no data modification
6. **No Data Fabrication** — The system never invents data or fake responses

---

## 📁 Project Structure

ZSolution/
│
├── config.py ← Central configuration
├── zsolution_init.py ← Entry point (FastAPI)
├── normalize_fa.py ← Persian text normalizer
├── requirements.txt
├── install.bat / run.bat
├── README.md
├── LICENSE
├── .gitignore
│
├── core/ ← Business logic
│ ├── init.py
│ ├── models.py ← Data contracts
│ └── orchestrator.py ← Conversation flow
│
├── stt/ ← Speech-to-text
│ ├── init.py
│ └── vosk_adapter.py
│
├── nlu/ ← Intent recognition
│ ├── init.py
│ └── rule_based.py
│
├── text2sql/ ← SQL generation
│ ├── init.py
│ └── mock_generator.py
│
├── sql_guard/ ← SQL validation
│ ├── init.py
│ └── validator.py
│
├── db/ ← Data access layer
│ ├── init.py
│ ├── base.py ← Abstract interface
│ └── mock_adapter.py
│
├── responder/ ← Response generation
│ ├── init.py
│ └── persian_builder.py
│
├── tts/ ← Text-to-speech
│ ├── init.py
│ └── pocket_tts_adapter.py
│
├── audio_utils/ ← Audio utilities
│ ├── init.py
│ └── ffmpeg_converter.py
│
├── ui/ ← Web interface
│ ├── init.py
│ ├── gradio_app.py ← Test page
│ └── main_page.py ← Main page
│
├── static/ ← Static assets
│ ├── main.css
│ └── main.js
│
├── logs/ ← Runtime logs (git-ignored)
│ ├── uploads/
│ └── responses/
│
├── models/ ← Downloaded models (git-ignored)
│ └── Homo-GE2PE-Persian-HF/
│
├── vosk/ ← Vosk model (git-ignored)
│ └── vosk-model-fa-0.5/
│
└── pocket-tts-farsi-v2/ ← TTS model (git-ignored)
└── model.yaml
text


---

## 📋 Requirements

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 | Windows 11 |
| **Python** | 3.12 | 3.12 |
| **RAM** | 8 GB | 16 GB |
| **Disk Space** | 2 GB | 4 GB |
| **CPU** | Dual-core | Quad-core |
| **GPU** | Not required | Optional (CUDA) |

### External Dependencies

- **FFmpeg** — Required for audio format conversion
  - Windows: `choco install ffmpeg` or [download from ffmpeg.org](https://ffmpeg.org/download.html)
  - Verify: `ffmpeg -version`

### Python Packages

See `requirements.txt`:

pocket-tts
transformers
vosk
numpy
soundfile
gradio
torch
tqdm
pyyaml
safetensors
tokenizers
scipy
fastapi
uvicorn
python-multipart
pydantic
text


---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/USERNAME/ZAI-Assistant.git
cd ZAI-Assistant

Step 2: Install FFmpeg

Windows (Chocolatey):
cmd

choco install ffmpeg

Windows (Manual):

    Download from ffmpeg.org

    Extract to C:\ffmpeg

    Add C:\ffmpeg\bin to your PATH

Verify:
cmd

ffmpeg -version

Step 3: Install Python 3.12

Download from python.org and install.
Step 4: Run the Installation Script
cmd

install.bat

This will:

    Create a virtual environment in .venv/

    Install all Python packages

    Install the Vosk prebuilt wheel

Step 5: Download Models

See Model Setup below.
📦 Model Setup

Three models are required. They are not included in the repository due to size, but all are freely available.
Model 1: Vosk Persian STT (~50 MB)

Download: alphacephei.com/vosk/models

    Choose: vosk-model-fa-0.5

Extract to:
text

vosk/vosk-model-fa-0.5/vosk-model-fa-0.5/

Expected structure:
text

vosk/vosk-model-fa-0.5/vosk-model-fa-0.5/
├── am/
├── conf/
├── graph/
├── ivector/
└── ...

Model 2: Pocket TTS Persian (~100 MB)

Place the model folder in:
text

pocket-tts-farsi-v2/

Expected structure:
text

pocket-tts-farsi-v2/
├── model.yaml
├── ...

Model 3: Homo-GE2PE Persian G2P (~250 MB)

Download automatically by running once:
powershell

python -c "from transformers import AutoTokenizer, T5ForConditionalGeneration; repo='mehdi-hf/Homo-GE2PE-Persian-HF'; path='models/Homo-GE2PE-Persian-HF'; AutoTokenizer.from_pretrained(repo).save_pretrained(path); T5ForConditionalGeneration.from_pretrained(repo).save_pretrained(path); print('Saved to:', path)"

Expected output:
text

Saved to: models/Homo-GE2PE-Persian-HF

Total Size
Model	Approximate Size
Vosk STT	~50 MB
Pocket TTS	~100 MB
G2P	~250 MB
Total	~400 MB
▶️ Running the App
Option 1: Using the Run Script
cmd

run.bat

Option 2: Manual Start
powershell

.venv\Scripts\activate
python zsolution_init.py

Expected Output
text

============================================================
  ZSolution — Persian Voice Assistant
============================================================

[1/3] Loading modules...
→ Loading Vosk model...
→ Vosk model loaded.
→ Loading TTS model...
→ Loading default voice...
→ Loading G2P model: models/Homo-GE2PE-Persian-HF
→ TTS adapter ready.

[2/3] Wiring orchestrator...

[3/3] Building UIs...

============================================================
  Main : http://127.0.0.1:7862/
  Test : http://127.0.0.1:7862/test
  API  : http://127.0.0.1:7862/api/voice
============================================================

Access URLs
URL	Purpose
http://127.0.0.1:7862/	Main page (auto VAD)
http://127.0.0.1:7862/test	Test page (manual form)
http://127.0.0.1:7862/api/voice	Voice API endpoint
http://127.0.0.1:7862/api/text	Text API endpoint
http://127.0.0.1:7862/api/health	Health check
http://127.0.0.1:7862/docs	Swagger UI
🎮 Usage
Main Page (Auto Mode)

    Open http://127.0.0.1:7862/

    Grant microphone access when prompted

    Speak your request

    Pause (1.2 seconds of silence) — the system auto-sends

    Wait for the response

    The answer is played automatically

    System returns to listening mode

Text Input

You can also type your request in the input bar at the bottom of the main page:

    Type your question

    Press Enter or click Send

    The response plays automatically

Test Page (Manual Mode)

Open http://127.0.0.1:7862/test for:

    Manual audio recording

    Direct text input

    Full technical details (intent, SQL, DB status)

    Voice cloning settings

Supported Commands
Command Type	Example	Response
Inventory query	«موجودی ورق فولادی در انبار مرکزی چقدر است؟»	Stock quantity
Item list	«لیست کالاها را بگو»	List of items
Warehouse list	«چه انبارهایی داریم؟»	List of warehouses
Greeting	«سلام»	Greeting response
Thanks	«ممنون»	Acknowledgment
Goodbye	«خداحافظ»	Farewell
Unknown	Any other input	Clarification request
🔌 API Reference
POST /api/voice

Receives an audio file, returns text response and audio URL.

Request:
text

Content-Type: multipart/form-data
Field: audio (file) — WebM, WAV, OGG, MP3, etc.

Response:
json

{
  "status": "success",
  "text": "موجودی ورق فولادی در انبار مرکزی برابر ۱۲۰۰ کیلوگرم است.",
  "audio_url": "/logs/responses/resp_abc123.wav",
  "intent": "inventory_query",
  "stt_text": "موجودی ورق فولادی در انبار مرکزی چقدر است"
}

POST /api/text

Receives text, returns response and audio URL.

Request:
json

{
  "text": "موجودی ورق فولادی در انبار مرکزی چقدر است؟"
}

Response:
json

{
  "status": "success",
  "text": "موجودی ورق فولادی در انبار مرکزی برابر ۱۲۰۰ کیلوگرم است.",
  "audio_url": "/logs/responses/resp_abc123.wav",
  "intent": "inventory_query",
  "stt_text": ""
}

GET /api/health

Response:
json

{
  "status": "ok",
  "orchestrator": true
}

Interactive API Docs

Visit http://127.0.0.1:7862/docs for full Swagger UI.
⚙️ Configuration

All settings are in config.py.
Model Paths
python

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOSK_MODEL_PATH = os.path.join(BASE_DIR, "vosk", "vosk-model-fa-0.5", "vosk-model-fa-0.5")
TTS_MODEL_PATH = os.path.join(BASE_DIR, "pocket-tts-farsi-v2", "model.yaml")
DEFAULT_VOICE_PATH = os.path.join(BASE_DIR, "example_voice.wav")
G2P_REPO = os.path.join(BASE_DIR, "models", "Homo-GE2PE-Persian-HF")

TTS Parameters
Parameter	Default	Description
TTS_TEMPERATURE	0.3	Sampling temperature
TTS_MAX_CHARS	100	Max characters per chunk
TTS_MIN_CHARS	30	Min characters per chunk
TTS_EOS_THRESHOLD	-4.0	End-of-speech threshold
TTS_YIELD_INTERVAL_SEC	0.5	Streaming yield interval
Server Settings
python

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7862

SQL Guard Limits
python

SQL_MAX_ROWS = 1000
SQL_MAX_LENGTH = 10000

VAD Parameters

Edit static/main.js:
javascript

const VAD_CONFIG = {
    SILENCE_THRESHOLD:   0.012,   // RMS threshold
    SILENCE_DURATION:    1200,    // ms of silence before sending
    MIN_SPEECH_DURATION: 400,     // Minimum speech duration
    MAX_RECORD_DURATION: 30000,   // Maximum recording duration
    EQ_BARS:             48,      // Equalizer bars
    MAX_HISTORY:         20,      // Max history items
};

Tuning Tips:
Environment	SILENCE_THRESHOLD	SILENCE_DURATION
Quiet room	0.008	1000
Normal	0.012	1200
Noisy	0.03	1500
📐 Data Contracts

All modules communicate via dataclass contracts defined in core/models.py.
ParsedRequest — NLU Output
python

@dataclass
class ParsedRequest:
    intent: str
    entities: dict
    operation: str = "read"
    filters: list = []
    confidence: float = 0.0
    requires_clarification: bool = False
    clarification_question: Optional[str] = None

SQLQuery — Text-to-SQL Output
python

@dataclass
class SQLQuery:
    sql: str
    params: dict
    operation: str
    explanation: str
    valid: bool

ValidationResult — SQL Guard Output
python

@dataclass
class ValidationResult:
    allowed: bool
    reason: Optional[str]
    sanitized_sql: str

QueryResult — Database Output
python

@dataclass
class QueryResult:
    status: str                # "ok" | "empty" | "error"
    columns: list
    rows: list
    row_count: int
    error: Optional[str]
    is_mock: bool

NaturalResponse — Responder Output
python

@dataclass
class NaturalResponse:
    text: str
    is_empty: bool
    error: Optional[str]

ConversationTurn — Final Output
python

@dataclass
class ConversationTurn:
    request_id: str
    recognized_text: str
    parsed_request: Optional[ParsedRequest]
    sql_query: Optional[SQLQuery]
    query_result: Optional[QueryResult]
    response_text: str
    audio_chunks: Optional[Any]

🔐 Security
Implemented Security Principles

    SQL Generation Separated from Execution — MockTextToSQL generates, MockDatabaseAdapter executes

    Mandatory Validation — SQLGuard runs before every execution

    Read-Only by Default — INSERT, UPDATE, DELETE are forbidden

    Length Limits — SQL_MAX_LENGTH enforced

    Row Limits — SQL_MAX_ROWS enforced

    No Real Database Connection — Phase 1 uses Mock only

    No Sensitive Data Logging — Audio files are deleted after use

Forbidden SQL Keywords
text

INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, CREATE,
GRANT, REVOKE, EXEC, EXECUTE, ATTACH, DETACH,
PRAGMA, VACUUM, REPLACE, MERGE, CALL

Production Recommendations

    Add authentication layer

    Enable HTTPS

    Implement rate limiting

    Add audit logging

    Encrypt communication channel

    Restrict table and column access

🐛 Troubleshooting
Microphone Not Working

Symptoms: No microphone access prompt, or permission denied.

Solutions:

    Check browser microphone permissions (chrome://settings/content/microphone)

    Ensure you're using http://127.0.0.1:7862/ (not an IP address)

    Reload the page

    Use Chrome or Edge (not Firefox for auto VAD)

Low STT Accuracy

Symptoms: Recognized text doesn't match spoken input.

Solutions:

    Verify FFmpeg is installed: ffmpeg -version

    Use a higher-quality microphone

    Record in a quieter environment

    Adjust SILENCE_THRESHOLD in static/main.js

    Consider a larger Vosk model

TTS is Slow

Solutions:

    Reduce TTS_MAX_CHARS to 80

    Reduce TTS_MIN_CHARS to 25

    Adjust TTS_EOS_THRESHOLD to -3.0

/test Returns 404

Cause: Incorrect mount order in zsolution_init.py.

Solution: Ensure /test is mounted before /:
python

gr.mount_gradio_app(app, test_iface, path="/test")
gr.mount_gradio_app(app, main_iface, path="/")

JS Not Executing

Cause: iface.load(js=...) requires an arrow function.

Solution: In ui/main_page.py:
python

js_call = "() => {\n" + js_body + "\n}"
iface.load(fn=None, inputs=None, outputs=None, js=js_call)

HuggingFace "Unauthenticated Requests" Warning

Cause: The G2P model is downloaded from HuggingFace.

Solution: Download it once locally (see Model Setup).
FFmpeg Not Found

Windows:
cmd

choco install ffmpeg

Or manually download and add to PATH.

Verify:
cmd

ffmpeg -version

🗺️ Roadmap
Phase 1 — Complete ✅

    ☑

    Project documentation
    ☑

    Text request processing
    ☑

    Mock database simulator
    ☑

    Text-to-SQL generation
    ☑

    SQL validation
    ☑

    Persian response generation
    ☑

    TTS integration
    ☑

    Full speech-to-speech pipeline
    ☑

    Auto VAD in browser
    ☑

    Modern web UI with history

Phase 2 — NLU Improvements

    □

    Add more intents:

        item_detail — Item details

        warehouse_detail — Warehouse details

        stock_alert — Low stock alerts

        supplier_query — Supplier lookup

        report_query — Reports
    □

    Optional: replace rule-based NLU with a light ML model

Phase 3 — Real Database

    □

    Replace MockDatabaseAdapter with SQLiteAdapter
    □

    Add PostgreSQLAdapter and SQLServerAdapter
    □

    Migrate from Mock to real without changing Orchestrator

Phase 4 — Conversation Management

    □

    Maintain context across conversation turns
    □

    Topic tracking
    □

    Follow-up questions

Phase 5 — Security & Deployment

    □

    Authentication
    □

    HTTPS
    □

    Rate limiting
    □

    Docker support
    □

    Full API documentation

Phase 6 — UX Improvements

    □

    More natural TTS voice
    □

    Advanced voice cloning
    □

    Smoother animations
    □

    Multi-language support

📄 License

This project is licensed under the MIT License — see the LICENSE file for details.
Third-Party Licenses
Component	License
Vosk STT Model	Apache 2.0
Pocket TTS	MIT
Homo-GE2PE-Persian	MIT
Vazirmatn Font	SIL OFL 1.1
Gradio	Apache 2.0
FastAPI	MIT

All dependencies use permissive licenses compatible with the MIT License.


## 🙏 Acknowledgments

This project would not be possible without the generous work of
the open-source community. Special thanks to:

### Models

- **[Vosk](https://alphacephei.com/vosk/)** — Offline speech recognition engine
  by Alpha Cephei, released under Apache 2.0.

- **[Pocket TTS](https://github.com/kyutai-labs/pocket-tts)** — Lightweight,
  high-quality text-to-speech engine by Kyutai Labs, released under MIT.

- **[Homo-GE2PE-Persian-HF](https://huggingface.co/mehdi-hf/Homo-GE2PE-Persian-HF)**
  — Persian Grapheme-to-Phoneme model by **Mehdi** ([@mehdi-hf](https://huggingface.co/mehdi-hf)).
  This model is the backbone of our Persian TTS pipeline — it converts
  normalized Persian text into accurate phoneme sequences, dramatically
  improving pronunciation quality. **A huge thank you to Mehdi for
  training and sharing this model freely with the community.**

### Frameworks & Tools

- **[Gradio](https://gradio.app/)** — Web UI framework
- **[FastAPI](https://fastapi.tiangolo.com/)** — Modern Python web framework
- **[PyTorch](https://pytorch.org/)** — Deep learning framework
- **[HuggingFace Transformers](https://huggingface.co/docs/transformers)** — Model loading and inference
- **[FFmpeg](https://ffmpeg.org/)** — Audio format conversion

### Fonts & Design

- **[Vazirmatn](https://github.com/rastikerdar/vazirmatn)** — Beautiful Persian font by Saber Rastikerdar
- **Microsoft Fluent Design** — UI inspiration

### Special Thanks

**Mehdi ([@mehdi-hf](https://huggingface.co/mehdi-hf))** — for the
`Homo-GE2PE-Persian-HF` model that powers our Persian grapheme-to-phoneme
conversion. Without this contribution, the Persian TTS quality in this
project would be significantly lower.

If you use this project, please also consider giving a ⭐ to the
upstream model repositories linked above.