# ============================================================
#  ZSolution - Main Page
#  Theme: Microsoft Dynamics 365 / Fluent 2.0
#  Layout: Two-column (Main + History + Help)
# ============================================================

import os
import gradio as gr


BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")


def _read_static(name: str) -> str:
    path = os.path.join(STATIC_DIR, name)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


HTML = """
<div class="zs-app">

    <!-- ==================== Command Bar ==================== -->
    <div class="zs-commandbar">
        <div class="zs-cmdbar-waffle" title="ZAI Assistant">
            <svg viewBox="0 0 20 20" fill="currentColor">
                <rect x="2" y="2" width="4" height="4"/>
                <rect x="8" y="2" width="4" height="4"/>
                <rect x="14" y="2" width="4" height="4"/>
                <rect x="2" y="8" width="4" height="4"/>
                <rect x="8" y="8" width="4" height="4"/>
                <rect x="14" y="8" width="4" height="4"/>
                <rect x="2" y="14" width="4" height="4"/>
                <rect x="8" y="14" width="4" height="4"/>
                <rect x="14" y="14" width="4" height="4"/>
            </svg>
        </div>
        <div class="zs-cmdbar-title">ZAI Assistant</div>
    </div>

    <!-- ==================== Body ==================== -->
    <div class="zs-body">

        <!-- ---------- Main Column (Left) ---------- -->
        <div class="zs-main-col">

            <!-- Status -->
            <div id="zs-status-card" class="zs-status-card ready">
                <div class="zs-status-icon">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6z"/>
                    </svg>
                </div>
                <div class="zs-status-body">
                    <div class="zs-status-label">STATUS</div>
                    <div id="zs-status-value" class="zs-status-value">آماده — گوش می‌دهم...</div>
                </div>
                <div id="zs-status-time" class="zs-status-time">00:00</div>
            </div>

            <!-- Equalizer -->
            <div class="zs-stage">
                <div id="zs-equalizer-wrap" class="zs-equalizer-wrap idle">
                    <div id="zs-equalizer" class="zs-equalizer idle"></div>
                </div>
                <div id="zs-hint" class="zs-hint">حرف بزنید یا تایپ کنید...</div>
            </div>

            <!-- Final Response -->
            <div id="zs-final-response" class="zs-final-response empty">
                <div class="zs-final-header">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H6l-4 4V5z"/>
                    </svg>
                    <span>پاسخ نهایی سرور</span>
                </div>
                <div id="zs-final-text" class="zs-final-text">
                    هنوز پاسخی دریافت نشده است.
                </div>
            </div>

            <!-- Text Input -->
            <div class="zs-input-bar">
                <input
                    id="zs-text-input"
                    class="zs-text-input"
                    type="text"
                    placeholder="متن خود را بنویسید و Enter بزنید..."
                    autocomplete="off"
                />
                <button id="zs-send-btn" class="zs-send-btn">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
                    </svg>
                    ارسال
                </button>
            </div>

        </div>

        <!-- ---------- History Column (Right) ---------- -->
        <div class="zs-history-col">

            <!-- ========== Help Panel ========== -->
            <div id="zs-help-panel" class="zs-help-panel">

                <div id="zs-help-toggle" class="zs-help-toggle">
                    <svg class="zs-help-icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"/>
                    </svg>
                    <div class="zs-help-title">راهنمای استفاده</div>
                    <svg class="zs-help-chevron" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/>
                    </svg>
                </div>

                <div class="zs-help-body">
                    <div class="zs-help-content">

                        <!-- نحوهٔ استفاده -->
                        <div class="zs-help-section">
                            <div class="zs-help-section-title">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6z"/>
                                </svg>
                                نحوهٔ استفاده
                            </div>
                            <ol class="zs-help-steps">
                                <li>روی کادر میکروفون کلیک کنید و اجازه بدهید.</li>
                                <li>حرف بزنید.</li>
                                <li>ساکت شوید (حدود ۱ ثانیه) — سیستم خودکار ارسال می‌کند.</li>
                                <li>پاسخ صوتی و متنی نمایش داده می‌شود.</li>
                            </ol>
                        </div>

                        <div class="zs-help-divider"></div>

                        <!-- نمونه دستورات -->
                        <div class="zs-help-section">
                            <div class="zs-help-section-title">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7z"/>
                                </svg>
                                نمونه دستورات
                            </div>
                            <ul class="zs-help-list">
                                <li>«موجودی ورق فولادی در انبار مرکزی چقدر است؟»</li>
                                <li>«لیست کالاها را بگو»</li>
                                <li>«چه انبارهایی داریم؟»</li>
                                <li>«سلام»</li>
                                <li>«ممنون»</li>
                                <li>«خداحافظ»</li>
                            </ul>
                        </div>

                        <div class="zs-help-divider"></div>

                        <!-- قابلیت تکرار -->
                        <div class="zs-help-section">
                            <div class="zs-help-section-title">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"/>
                                </svg>
                                قابلیت تکرار
                            </div>
                            <ul class="zs-help-list">
                                <li>اگر در پایان جمله <code>«تکرار کن»</code> بگویید،
                                    سیستم کل متن شما را به‌صورت صوتی تکرار می‌کند.</li>
                                <li>عبارت‌های مشابه: <code>«دوباره بگو»</code> و
                                    <code>«بگو دوباره»</code> نیز کار می‌کنند.</li>
                            </ul>
                            <div class="zs-help-example">
                                <b>مثال:</b> «امروز هوا خوب است، تکرار کن» →<br>
                                سیستم می‌گوید: «امروز هوا خوب است»
                            </div>
                        </div>

                        <div class="zs-help-divider"></div>

                        <!-- نکات -->
                        <div class="zs-help-section">
                            <div class="zs-help-section-title">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"/>
                                </svg>
                                نکات
                            </div>
                            <ul class="zs-help-list">
                                <li>می‌توانید به‌جای صحبت کردن، متنتان را در کادر پایین تایپ کنید و Enter بزنید.</li>
                                <li>برای شنیدن پاسخ قبلی، روی آیکون 🔵 در تاریخچه کلیک کنید.</li>
                                <li>برای پاک کردن تاریخچه، دکمهٔ «پاک کردن» پایین پنل را بزنید.</li>
                            </ul>
                        </div>

                    </div>
                </div>

            </div>

            <!-- ========== History Header ========== -->
            <div class="zs-history-header">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"/>
                </svg>
                <div class="zs-history-title">تاریخچه مکالمه</div>
                <div id="zs-history-count" class="zs-history-count">0</div>
            </div>

            <!-- ========== History List ========== -->
            <div id="zs-history-list" class="zs-history-list">
                <div id="zs-history-empty" class="zs-history-empty">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"/>
                    </svg>
                    <div>هنوز مکالمه‌ای شروع نشده است</div>
                </div>
            </div>

            <!-- ========== History Footer ========== -->
            <div class="zs-history-footer">
                <button id="zs-clear-btn" class="zs-clear-btn">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"/>
                    </svg>
                    پاک کردن تاریخچه
                </button>
            </div>

        </div>

    </div>

</div>

<!-- Overlay -->
<div id="zs-overlay" class="zs-overlay hidden">
    <div class="zs-overlay-card">
        <div class="zs-overlay-icon">
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
            </svg>
        </div>
        <h2 id="zs-overlay-title">در حال راه‌اندازی...</h2>
        <p id="zs-overlay-msg">لطفاً اجازه دسترسی به میکروفون را بدهید.</p>
        <button>تلاش مجدد</button>
    </div>
</div>

<div id="zs-debug" class="zs-debug"></div>
"""


def build_main_page():

    css = _read_static("main.css")
    js_body = _read_static("main.js")

    js_call = "() => {\n" + js_body + "\n}"

    with gr.Blocks(
        title="ZAI Assistant — دستیار صوتی هوشمند",
        css=css,
    ) as iface:
        gr.HTML(HTML)
        iface.load(fn=None, inputs=None, outputs=None, js=js_call)

    return iface