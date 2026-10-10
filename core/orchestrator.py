# ============================================================
#  ZSolution - Orchestrator
#  مدیریت جریان مکالمه: STT → NLU → Text2SQL → Guard → DB → Responder → TTS
# ============================================================

import uuid

from core.models import (
    ConversationTurn,
    NaturalResponse,
    ParsedRequest,
    QueryResult,
    SQLQuery,
)


class Orchestrator:
    """هماهنگ‌کنندهٔ تمام ماژول‌ها."""

    # --------------------------------------------------------
    #  intentهایی که بدون SQL پاسخ می‌گیرند
    # --------------------------------------------------------
    DIRECT_INTENTS = ("greeting", "thanks", "goodbye", "repeat")

    def __init__(self, stt, nlu, text2sql, guard, db, responder, tts):
        self.stt = stt
        self.nlu = nlu
        self.text2sql = text2sql
        self.guard = guard
        self.db = db
        self.responder = responder
        self.tts = tts

    # --------------------------------------------------------
    #  API عمومی
    # --------------------------------------------------------
    def handle_audio(self, audio_path: str) -> ConversationTurn:
        """جریان کامل از فایل صوتی تا پاسخ صوتی."""
        rid = self._new_id()
        print(f"[{rid}] ▶ Start (audio)")

        # ۱) STT
        print(f"[{rid}] STT ...")
        try:
            text = self.stt.transcribe(audio_path)
        except Exception as e:
            print(f"[{rid}] ! STT failed: {e}")
            return self._error_turn(rid, "", f"خطای STT: {e}")

        print(f"[{rid}] STT result: {text!r}")

        if not text or not text.strip():
            return self._finalize(
                rid, "", None, None, None,
                NaturalResponse(
                    text="چیزی شنیده نشد. لطفاً دوباره تلاش کنید.",
                    is_empty=True,
                ),
            )

        return self.handle_text(text, rid)

    def handle_text(self, text: str, rid: str = None) -> ConversationTurn:
        """جریان کامل از متن تا پاسخ صوتی."""
        rid = rid or self._new_id()
        print(f"[{rid}] ▶ Start (text): {text!r}")

        # ۲) NLU
        print(f"[{rid}] NLU ...")
        try:
            request = self.nlu.parse(text)
        except Exception as e:
            print(f"[{rid}] ! NLU failed: {e}")
            return self._error_turn(rid, text, f"خطای NLU: {e}")

        print(
            f"[{rid}] intent={request.intent} "
            f"entities={request.entities} "
            f"conf={request.confidence}"
        )

        # نیاز به شفاف‌سازی
        if request.requires_clarification:
            msg = (request.clarification_question
                   or "لطفاً درخواست خود را واضح‌تر بفرمایید.")
            return self._finalize(
                rid, text, request, None, None,
                NaturalResponse(text=msg, is_empty=False),
            )

        # ۳) intentهای بدون نیاز به SQL (greeting, thanks, goodbye, repeat)
        if request.intent in self.DIRECT_INTENTS:
            print(f"[{rid}] direct response (no SQL)")
            try:
                empty_result = QueryResult(
                    status="empty",
                    columns=[],
                    rows=[],
                    row_count=0,
                )
                response = self.responder.build(empty_result, request)
            except Exception as e:
                print(f"[{rid}] ! Responder failed: {e}")
                return self._error_turn(
                    rid, text, f"خطای ساخت پاسخ: {e}", request=request
                )

            return self._finalize(
                rid, text, request, None, None, response,
            )

        # ۴) Text-to-SQL (Mock)
        print(f"[{rid}] Text-to-SQL ...")
        try:
            sql_query = self.text2sql.generate(request)
        except Exception as e:
            print(f"[{rid}] ! Text2SQL failed: {e}")
            return self._error_turn(
                rid, text, f"خطای تولید SQL: {e}", request=request
            )

        if not sql_query.valid:
            return self._finalize(
                rid, text, request, sql_query, None,
                NaturalResponse(
                    text=sql_query.explanation or "کوئری قابل تولید نبود.",
                    is_empty=True,
                ),
            )

        print(f"[{rid}] SQL: {sql_query.sql[:80]}...")
        print(f"[{rid}] params: {sql_query.params}")

        # ۵) SQL Guard
        print(f"[{rid}] SQL Guard ...")
        validation = self.guard.validate(sql_query.sql)
        if not validation.allowed:
            msg = f"کوئری مجاز نیست: {validation.reason}"
            print(f"[{rid}] ! {msg}")
            return self._finalize(
                rid, text, request, sql_query, None,
                NaturalResponse(text=msg, is_empty=False),
            )

        # ۶) اجرای دیتابیس (Mock)
        print(f"[{rid}] DB execute ...")
        try:
            db_result = self.db.execute(
                validation.sanitized_sql,
                sql_query.params,
                request.intent,
            )
        except Exception as e:
            print(f"[{rid}] ! DB failed: {e}")
            return self._error_turn(
                rid, text, f"خطای دیتابیس: {e}",
                request=request, sql_query=sql_query,
            )

        print(
            f"[{rid}] DB status={db_result.status} "
            f"rows={db_result.row_count} "
            f"mock={db_result.is_mock}"
        )

        # ۷) Responder
        print(f"[{rid}] Responder ...")
        try:
            response = self.responder.build(db_result, request)
        except Exception as e:
            print(f"[{rid}] ! Responder failed: {e}")
            return self._error_turn(
                rid, text, f"خطای ساخت پاسخ: {e}",
                request=request, sql_query=sql_query,
                db_result=db_result,
            )

        print(f"[{rid}] Response: {response.text!r}")

        # ۸) TTS
        return self._finalize(
            rid, text, request, sql_query, db_result, response,
        )

    # --------------------------------------------------------
    #  internal
    # --------------------------------------------------------
    @staticmethod
    def _new_id() -> str:
        return uuid.uuid4().hex[:8]

    def _error_turn(self, rid, text, msg,
                    request=None, sql_query=None, db_result=None):
        """ساخت Turn خطا با TTS روی پیام خطا."""
        response = NaturalResponse(text=msg, is_empty=False, error=msg)
        return self._finalize(
            rid, text, request, sql_query, db_result, response,
        )

    def _finalize(self, rid, text, request, sql_query, db_result, response):
        """ساخت Turn نهایی + تولید صدا."""
        audio_chunks = None
        try:
            if response and response.text:
                print(f"[{rid}] TTS ...")
                audio_chunks = self.tts.synthesize(response.text)
        except Exception as e:
            print(f"[{rid}] ! TTS failed: {e}")

        return ConversationTurn(
            request_id=rid,
            recognized_text=text or "",
            parsed_request=request,
            sql_query=sql_query,
            query_result=db_result,
            response_text=response.text if response else "",
            audio_chunks=audio_chunks,
        )