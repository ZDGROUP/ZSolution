# ============================================================
#  ZSolution - Data Contracts
#  قراردادهای داده بین ماژول‌ها
# ============================================================

from dataclasses import dataclass, field
from typing import Any, Optional


# ============================================================
#  خروجی NLU
# ============================================================
@dataclass
class ParsedRequest:
    """درخواست تحلیل‌شدهٔ کاربر."""
    intent: str
    entities: dict = field(default_factory=dict)
    operation: str = "read"
    filters: list = field(default_factory=list)
    confidence: float = 0.0
    requires_clarification: bool = False
    clarification_question: Optional[str] = None


# ============================================================
#  خروجی Text-to-SQL
# ============================================================
@dataclass
class SQLQuery:
    """کوئری SQL تولیدشده."""
    sql: str
    params: dict = field(default_factory=dict)
    operation: str = "read"
    explanation: str = ""
    valid: bool = True


# ============================================================
#  خروجی SQL Guard
# ============================================================
@dataclass
class ValidationResult:
    """نتیجهٔ اعتبارسنجی SQL."""
    allowed: bool
    reason: Optional[str] = None
    sanitized_sql: str = ""


# ============================================================
#  خروجی Database
# ============================================================
@dataclass
class QueryResult:
    """نتیجهٔ اجرای کوئری."""
    status: str                          # "ok" | "empty" | "error"
    columns: list = field(default_factory=list)
    rows: list = field(default_factory=list)
    row_count: int = 0
    error: Optional[str] = None
    is_mock: bool = True


# ============================================================
#  خروجی Responder
# ============================================================
@dataclass
class NaturalResponse:
    """پاسخ نهایی به فارسی."""
    text: str
    is_empty: bool = False
    error: Optional[str] = None


# ============================================================
#  خروجی نهایی هر Turn مکالمه
# ============================================================
@dataclass
class ConversationTurn:
    """یک دور کامل مکالمه."""
    request_id: str
    recognized_text: str
    parsed_request: Optional[ParsedRequest] = None
    sql_query: Optional[SQLQuery] = None
    query_result: Optional[QueryResult] = None
    response_text: str = ""
    audio_chunks: Optional[Any] = None