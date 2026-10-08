/* ============================================================
   ZSolution — Main Page Script
   VAD + MediaRecorder + Text Input + History
   ============================================================ */

const VAD_CONFIG = {
    SILENCE_THRESHOLD:   0.012,
    SILENCE_DURATION:    1200,
    MIN_SPEECH_DURATION: 400,
    MAX_RECORD_DURATION: 30000,
    EQ_BARS:             48,
    MAX_HISTORY:         20,
};

const state = {
    recording:    false,
    audioCtx:     null,
    analyser:     null,
    stream:       null,
    silenceStart: null,
    speechStart:  null,
    sampleRate:   16000,
    eqBars:       [],
    status:       'ready',
    startTime:    null,
    history:      [],
    busy:         false,
};

let mediaRecorder = null;
let audioChunks   = [];

const $ = (id) => document.getElementById(id);

const el = {};

function refreshEls() {
    el.card         = $('zs-status-card');
    el.statusVal    = $('zs-status-value');
    el.statusTime   = $('zs-status-time');
    el.eqWrap       = $('zs-equalizer-wrap');
    el.eq           = $('zs-equalizer');
    el.hint         = $('zs-hint');
    el.finalResp    = $('zs-final-response');
    el.finalText    = $('zs-final-text');
    el.textInput    = $('zs-text-input');
    el.sendBtn      = $('zs-send-btn');
    el.historyList  = $('zs-history-list');
    el.historyEmpty = $('zs-history-empty');
    el.historyCount = $('zs-history-count');
    el.clearBtn     = $('zs-clear-btn');
    el.overlay      = $('zs-overlay');
    el.overlayT     = $('zs-overlay-title');
    el.overlayP     = $('zs-overlay-msg');
    el.debug        = $('zs-debug');
}

const STATUS_MAP = {
    ready:      { label: 'آماده — گوش می‌دهم...',  cls: 'ready',      hint: 'حرف بزنید یا تایپ کنید...' },
    inRecord:   { label: 'در حال ضبط صدا',          cls: 'inRecord',   hint: '🎙️ صحبت کنید...' },
    sending:    { label: 'ارسال به سرور',           cls: 'sending',    hint: '📤 در حال ارسال...' },
    processing: { label: 'در حال پردازش درخواست',  cls: 'processing', hint: '⚙️ لطفاً صبر کنید...' },
    playAnswer: { label: 'در حال پخش پاسخ',         cls: 'playAnswer', hint: '🔊 پاسخ:' },
};

function setStatus(key) {
    const cfg = STATUS_MAP[key] || STATUS_MAP.ready;
    state.status = key;

    if (el.card)      el.card.className       = 'zs-status-card ' + cfg.cls;
    if (el.statusVal) el.statusVal.textContent = cfg.label;
    if (el.hint) {
        el.hint.className = 'zs-hint ' + cfg.cls;
        el.hint.textContent = cfg.hint;
    }
    if (el.eq)     el.eq.className     = 'zs-equalizer ' + cfg.cls;
    if (el.eqWrap) el.eqWrap.className = 'zs-equalizer-wrap ' + cfg.cls;
}

function showFinalResponse(text) {
    if (!el.finalResp) return;
    if (!text) {
        el.finalText.textContent = 'هنوز پاسخی دریافت نشده است.';
        el.finalResp.classList.add('empty');
        return;
    }
    el.finalText.textContent = text;
    el.finalResp.classList.remove('empty');
}

function debug(msg) {
    console.log('[ZS]', msg);
    if (el.debug) el.debug.textContent = String(msg).slice(0, 200);
}

// ---------- Timer ----------
function startTimer() {
    if (state.startTime) return;
    state.startTime = Date.now();
    updateTimer();
}

function updateTimer() {
    if (!state.startTime) return;
    const sec = Math.floor((Date.now() - state.startTime) / 1000);
    const mm  = String(Math.floor(sec / 60)).padStart(2, '0');
    const ss  = String(sec % 60).padStart(2, '0');
    if (el.statusTime) el.statusTime.textContent = mm + ':' + ss;
    if (state.recording) requestAnimationFrame(updateTimer);
}

function resetTimer() {
    state.startTime = null;
    if (el.statusTime) el.statusTime.textContent = '00:00';
}

// ---------- Equalizer ----------
function buildEqualizer() {
    if (!el.eq) return;
    el.eq.innerHTML = '';
    state.eqBars = [];
    for (let i = 0; i < VAD_CONFIG.EQ_BARS; i++) {
        const b = document.createElement('div');
        b.className = 'zs-eq-bar';
        el.eq.appendChild(b);
        state.eqBars.push(b);
    }
}

function updateEqualizer(freqData) {
    const N = state.eqBars.length;
    if (!N || !freqData) return;
    const step = Math.floor(freqData.length / N);
    for (let i = 0; i < N; i++) {
        const v = freqData[i * step] / 255;
        const h = Math.max(6, Math.min(120, v * 120));
        state.eqBars[i].style.height = h + 'px';
    }
}

// ============================================================
//  History
// ============================================================
function formatTime() {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    return hh + ':' + mm;
}

function addHistory(role, text, audioUrl) {
    if (!text) return;

    state.history.push({
        role: role,
        text: text,
        time: formatTime(),
        audioUrl: audioUrl || null,
    });

    // حداکثر ۲۰ پیام آخر
    if (state.history.length > VAD_CONFIG.MAX_HISTORY) {
        state.history = state.history.slice(-VAD_CONFIG.MAX_HISTORY);
    }

    renderHistory();
}

function renderHistory() {
    if (!el.historyList) return;

    // اگر خالی است
    if (state.history.length === 0) {
        el.historyList.innerHTML = '';
        if (el.historyEmpty) {
            el.historyEmpty.style.display = 'flex';
            el.historyList.appendChild(el.historyEmpty);
        }
    } else {
        if (el.historyEmpty) el.historyEmpty.style.display = 'none';

        // فقط پیام‌های جدید اضافه می‌کنیم (بهبود کارایی)
        const existing = el.historyList.querySelectorAll('.zs-msg').length;
        const missing = state.history.slice(existing);

        for (const item of missing) {
            el.historyList.appendChild(buildMessageEl(item));
        }

        // اگر تعداد بیشتر از پیام‌های نمایش داده‌شده بود، کاملاً rebuild
        if (existing > state.history.length) {
            el.historyList.innerHTML = '';
            for (const item of state.history) {
                el.historyList.appendChild(buildMessageEl(item));
            }
        }
    }

    // اسکرول به پایین
    el.historyList.scrollTop = el.historyList.scrollHeight;

    // به‌روزرسانی شمارنده
    if (el.historyCount) {
        el.historyCount.textContent = state.history.length;
    }
}

function buildMessageEl(item) {
    const wrap = document.createElement('div');
    wrap.className = 'zs-msg ' + (item.role === 'user' ? 'user' : 'zai');

    const header = document.createElement('div');
    header.className = 'zs-msg-header';

    const author = document.createElement('div');
    author.className = 'zs-msg-author';
    author.textContent = item.role === 'user' ? '👤 شما' : '🤖 ZAI';

    const time = document.createElement('div');
    time.className = 'zs-msg-time';
    time.textContent = item.time;

    header.appendChild(author);
    header.appendChild(time);

    const body = document.createElement('div');
    body.className = 'zs-msg-body';
    body.textContent = item.text;

    // دکمهٔ پخش صدا (فقط برای پیام ZAI)
    if (item.role !== 'user' && item.audioUrl) {
        const playBtn = document.createElement('button');
        playBtn.className = 'zs-msg-play';
        playBtn.title = 'پخش صدا';
        playBtn.innerHTML = `
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path d="M6 4l10 6-10 6V4z"/>
            </svg>
        `;
        playBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            playHistoryAudio(item.audioUrl, playBtn);
        });
        body.appendChild(playBtn);
    }

    wrap.appendChild(header);
    wrap.appendChild(body);
    return wrap;
}

let currentPlayingBtn = null;

function playHistoryAudio(url, btn) {
    // اگر همان دکمه در حال پخش است → متوقف کن
    if (currentPlayingBtn === btn) {
        if (currentAudio) currentAudio.pause();
        return;
    }

    // توقف پخش قبلی
    if (currentAudio) {
        currentAudio.pause();
        if (currentPlayingBtn) currentPlayingBtn.classList.remove('playing');
    }

    currentAudio = new Audio(url);
    currentPlayingBtn = btn;
    btn.classList.add('playing');

    currentAudio.onended = () => {
        btn.classList.remove('playing');
        currentPlayingBtn = null;
    };

    currentAudio.onerror = () => {
        btn.classList.remove('playing');
        currentPlayingBtn = null;
    };

    currentAudio.play().catch(() => {
        btn.classList.remove('playing');
        currentPlayingBtn = null;
    });
}

let currentAudio = null;

function clearHistory() {
    state.history = [];
    renderHistory();
}

// ============================================================
//  Recording
// ============================================================
async function startRecording() {
    if (state.recording || state.busy) return;

    try {
        state.stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl:  true,
                channelCount: 1,
            }
        });

        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        await audioCtx.resume();
        const source   = audioCtx.createMediaStreamSource(state.stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);

        const mimeOptions = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4',
        ];
        let chosenMime = '';
        for (const m of mimeOptions) {
            if (MediaRecorder.isTypeSupported(m)) {
                chosenMime = m;
                break;
            }
        }

        mediaRecorder = new MediaRecorder(state.stream, {
            mimeType: chosenMime || undefined,
            audioBitsPerSecond: 128000,
        });

        audioChunks = [];
        mediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) audioChunks.push(e.data);
        };

        state.audioCtx     = audioCtx;
        state.analyser     = analyser;
        state.recording    = true;
        state.silenceStart = null;
        state.speechStart  = null;
        state.sampleRate   = audioCtx.sampleRate;

        mediaRecorder.start(100);

        setStatus('inRecord');
        resetTimer();
        startTimer();

        const timeData  = new Float32Array(analyser.fftSize);
        const freqData  = new Uint8Array(analyser.frequencyBinCount);
        const startTime = performance.now();

        function loop() {
            if (!state.recording) return;

            if (performance.now() - startTime > VAD_CONFIG.MAX_RECORD_DURATION) {
                finalizeRecording();
                return;
            }

            analyser.getFloatTimeDomainData(timeData);
            analyser.getByteFrequencyData(freqData);
            updateEqualizer(freqData);

            let sum = 0;
            for (let i = 0; i < timeData.length; i++) sum += timeData[i] * timeData[i];
            const rms = Math.sqrt(sum / timeData.length);

            const now = performance.now();

            if (rms > VAD_CONFIG.SILENCE_THRESHOLD) {
                state.silenceStart = null;
                if (!state.speechStart) state.speechStart = now;
            } else {
                if (state.speechStart) {
                    if (!state.silenceStart) {
                        state.silenceStart = now;
                    } else if (now - state.silenceStart > VAD_CONFIG.SILENCE_DURATION) {
                        const speechDur = now - state.speechStart;
                        if (speechDur >= VAD_CONFIG.MIN_SPEECH_DURATION) {
                            finalizeRecording();
                            return;
                        } else {
                            state.silenceStart = null;
                            state.speechStart  = null;
                        }
                    }
                }
            }

            requestAnimationFrame(loop);
        }
        requestAnimationFrame(loop);

    } catch (err) {
        debug('getUserMedia error: ' + err.message);
        showOverlay('خطای میکروفون',
            'دسترسی به میکروفون رد شد.\nلطفاً از تنظیمات مرورگر اجازه بدهید.',
            () => location.reload());
    }
}

function finalizeRecording() {
    if (!state.recording) return;
    state.recording = false;

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.onstop = () => {
            const blob = new Blob(audioChunks, { type: 'audio/webm' });
            debug('recorded ' + blob.size + ' bytes');

            if (state.stream) {
                state.stream.getTracks().forEach(t => t.stop());
                state.stream = null;
            }
            if (state.audioCtx) {
                state.audioCtx.close().catch(()=>{});
                state.audioCtx = null;
            }

            if (blob.size < 1000) {
                debug('audio too small');
                setStatus('ready');
                resetTimer();
                setTimeout(startRecording, 500);
                return;
            }

            sendAudioToServer(blob);
        };
        mediaRecorder.stop();
    } else {
        setStatus('ready');
        resetTimer();
        setTimeout(startRecording, 500);
    }
}

// ============================================================
//  Send to server — Audio
// ============================================================
async function sendAudioToServer(blob) {
    setStatus('sending');
    state.busy = true;

    try {
        const form = new FormData();
        form.append('audio', blob, 'recording.webm');

        const res = await fetch('/api/voice', {
            method: 'POST',
            body: form,
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error('server ' + res.status + ': ' + errText.slice(0, 200));
        }

        setStatus('processing');

        const result = await res.json();
        handleServerResult(result);

    } catch (err) {
        debug('send error: ' + err.message);
        showOverlay('خطای ارتباط با سرور',
            err.message,
            () => { hideOverlay(); setStatus('ready'); resetTimer(); state.busy = false; setTimeout(startRecording, 500); });
    }
}

// ============================================================
//  Send to server — Text
// ============================================================
async function sendTextToServer(text) {
    if (!text || !text.trim()) return;
    if (state.busy) return;

    state.busy = true;
    setStatus('sending');

    // افزودن پیام کاربر به History فوراً
    addHistory('user', text.trim(), null);

    try {
        const res = await fetch('/api/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text.trim() }),
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error('server ' + res.status + ': ' + errText.slice(0, 200));
        }

        setStatus('processing');

        const result = await res.json();
        handleServerResult(result, true);   // skipUserHistory = true

    } catch (err) {
        debug('send error: ' + err.message);
        showOverlay('خطای ارتباط با سرور',
            err.message,
            () => { hideOverlay(); setStatus('ready'); resetTimer(); state.busy = false; setTimeout(startRecording, 500); });
    }
}

// ============================================================
//  Handle server response
// ============================================================
function handleServerResult(result, skipUserHistory) {
    debug('reply: ' + JSON.stringify(result).slice(0, 200));

    // متن پاسخ
    if (result.text) {
        showFinalResponse(result.text);
        // افزودن به History اگر از سمت صدا آمده (چون در متن، بالا اضافه شد)
        if (!skipUserHistory) {
            // پیام کاربر: از STT
            if (result.stt_text) {
                addHistory('user', result.stt_text, null);
            }
            addHistory('zai', result.text, result.audio_url || null);
        } else {
            addHistory('zai', result.text, result.audio_url || null);
        }
    }

    // پخش صدا
    if (result.audio_url) {
        playAudio(result.audio_url);
    } else {
        setStatus('ready');
        resetTimer();
        state.busy = false;
        setTimeout(startRecording, 800);
    }
}

function playAudio(url) {
    setStatus('playAnswer');
    const audio = new Audio(url);

    audio.onended = () => {
        setStatus('ready');
        resetTimer();
        state.busy = false;
        setTimeout(startRecording, 500);
    };

    audio.onerror = () => {
        setStatus('ready');
        resetTimer();
        state.busy = false;
        setTimeout(startRecording, 500);
    };

    audio.play().catch(() => {
        setStatus('ready');
        resetTimer();
        state.busy = false;
        setTimeout(startRecording, 500);
    });
}

// ============================================================
//  Overlay
// ============================================================
function showOverlay(title, msg, action) {
    if (!el.overlay) return;
    el.overlayT.textContent = title;
    el.overlayP.textContent = msg;
    el.overlay.classList.remove('hidden');
    const btn = el.overlay.querySelector('button');
    if (btn && action) {
        btn.onclick = action;
        btn.style.display = 'inline-flex';
    } else if (btn) {
        btn.style.display = 'none';
    }
}

function hideOverlay() {
    if (el.overlay) el.overlay.classList.add('hidden');
}

// ============================================================
//  Text input events
// ============================================================
function setupTextInput() {
    if (!el.sendBtn || !el.textInput) return;

    el.sendBtn.addEventListener('click', () => {
        const text = el.textInput.value.trim();
        if (!text) return;
        el.textInput.value = '';
        sendTextToServer(text);
    });

    el.textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            el.sendBtn.click();
        }
    });
}

// ============================================================
//  Init
// ============================================================
(async function init() {
    refreshEls();
    debug('init called');

    setupTextInput();

    if (el.clearBtn) {
        el.clearBtn.addEventListener('click', clearHistory);
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showOverlay('مرورگر پشتیبانی نمی‌کند',
            'مرورگر شما از API میکروفون پشتیبانی نمی‌کند.\nلطفاً از Chrome یا Edge استفاده کنید.',
            null);
        return;
    }

    buildEqualizer();
    setStatus('ready');
    showFinalResponse('');

    try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        await startRecording();
    } catch (err) {
        debug('permission error: ' + err.message);
        showOverlay('دسترسی به میکروفون لازم است',
            'برای استفاده از دستیار، لطفاً به میکروفون دسترسی بدهید.\nسپس صفحه را دوباره بارگذاری کنید.',
            () => location.reload());
    }
})();