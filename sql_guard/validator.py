# ============================================================
#  ZSolution - SQL Guard
#  اعتبارسنجی کوئری — فقط SELECT مجاز
# ============================================================

import re

import config
from core.models import ValidationResult


class SQLGuard:
    """اعتبارسنجی SQL قبل از اجرا."""

    # --------------------------------------------------------
    #  کلمات ممنوع
    # --------------------------------------------------------
    FORBIDDEN_KEYWORDS = re.compile(
        r"\b("
        r"INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|"
        r"GRANT|REVOKE|EXEC|EXECUTE|ATTACH|DETACH|PRAGMA|VACUUM|"
        r"REPLACE|MERGE|CALL"
        r")\b",
        re.IGNORECASE,
    )

    # --------------------------------------------------------
    #  API عمومی
    # --------------------------------------------------------
    def validate(self, sql: str) -> ValidationResult:
        """SQL را بررسی می‌کند و ValidationResult برمی‌گرداند."""
        if not sql or not sql.strip():
            return ValidationResult(
                allowed=False,
                reason="کوئری خالی است.",
                sanitized_sql="",
            )

        s = sql.strip().rstrip(";").strip()

        # بررسی طول
        if len(s) > config.SQL_MAX_LENGTH:
            return ValidationResult(
                allowed=False,
                reason=(
                    f"طول کوئری از حد مجاز "
                    f"({config.SQL_MAX_LENGTH} کاراکتر) بیشتر است."
                ),
                sanitized_sql="",
            )

        # بررسی چند دستور در یک کوئری
        if ";" in s:
            return ValidationResult(
                allowed=False,
                reason="چند دستور در یک کوئری مجاز نیست.",
                sanitized_sql="",
            )

        # بررسی کلمات ممنوع
        if self.FORBIDDEN_KEYWORDS.search(s):
            return ValidationResult(
                allowed=False,
                reason="فقط عملیات خواندن (SELECT) مجاز است.",
                sanitized_sql="",
            )

        # بررسی شروع کوئری
        first_word = s.split(None, 1)[0].upper() if s else ""
        if first_word not in ("SELECT", "WITH"):
            return ValidationResult(
                allowed=False,
                reason="کوئری باید با SELECT یا WITH شروع شود.",
                sanitized_sql="",
            )

        # اعمال LIMIT اگر نبود
        sanitized = s
        if "LIMIT" not in s.upper():
            sanitized = f"{s} LIMIT {config.SQL_MAX_ROWS}"

        return ValidationResult(
            allowed=True,
            reason=None,
            sanitized_sql=sanitized,
        )