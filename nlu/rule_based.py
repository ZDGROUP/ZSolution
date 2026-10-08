# ============================================================
#  ZSolution - Rule-Based NLU
#  تحلیل درخواست فارسی بدون LLM — سریع و قابل تست
# ============================================================

import re

from core.models import ParsedRequest


class RuleBasedNLU:
    """تحلیل intent و entities با الگوهای ساده."""

    # --------------------------------------------------------
    #  جداول شناخته‌شده (برای تطبیق fuzzy)
    # --------------------------------------------------------
    KNOWN_ITEMS = [
        "ورق فولادی",
        "میلگرد",
        "تیرآهن",
        "لوله",
        "پروفیل",
    ]

    KNOWN_WAREHOUSES = [
        "انبار مرکزی",
        "انبار شمال",
        "انبار جنوب",
    ]

    # --------------------------------------------------------
    #  الگوهای intent (regex روی متن فارسی)
    # --------------------------------------------------------
    INTENT_PATTERNS = {
        "inventory_query": [
            r"موجودی\s+(.+?)\s+(?:در|توی|داخل|تویِ)\s+(.+?)(?:\s+چقدر|\s+چیه|\s+چیست|\s+هست|\?|$)",
            r"چقدر\s+(.+?)\s+(?:در|توی|داخل)\s+(.+?)(?:\s+داریم|\s+هست|\?|$)",
            r"(.+?)\s+(?:در|توی|داخل)\s+(.+?)\s+چقدر",
        ],
        "item_list": [
            r"(?:لیست|فهرست|همهٔ|همه)\s+کالا",
            r"چه\s+کالاهایی",
            r"چه\s+کالایی",
        ],
        "warehouse_list": [
            r"(?:لیست|فهرست|همهٔ|همه)\s+انبار",
            r"چه\s+انبارهایی",
            r"چند\s+انبار",
        ],
        "greeting": [
            r"^\s*(سلام|درود|صبح\s+بخیر|عصر\s+بخیر|شب\s+بخیر)",
        ],
        "thanks": [
            r"(ممنون|متشکر|سپاس)",
        ],
        "goodbye": [
            r"(خداحافظ|خدانگهدار|بای\s+بای|بای)",
        ],
    }

    # --------------------------------------------------------
    #  API عمومی
    # --------------------------------------------------------
    def parse(self, text: str) -> ParsedRequest:
        """متن را تحلیل می‌کند و ParsedRequest برمی‌گرداند."""
        if not text or not text.strip():
            return self._unknown()

        text = text.strip()

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                m = re.search(pattern, text, flags=re.IGNORECASE)
                if m:
                    return self._build(intent, m, text)

        return self._unknown()

    # --------------------------------------------------------
    #  ساخت ParsedRequest بر اساس intent
    # --------------------------------------------------------
    def _build(self, intent, match, full_text) -> ParsedRequest:
        entities = {}

        if intent == "inventory_query":
            groups = match.groups()
            if len(groups) >= 2:
                entities["item_name"]      = self._match_item(groups[0])
                entities["warehouse_name"] = self._match_warehouse(groups[1])
            else:
                # اگر regex فقط یک گروه گرفته بود، تلاش دوم
                entities["item_name"]      = self._match_item(full_text)
                entities["warehouse_name"] = self._match_warehouse(full_text)

            return ParsedRequest(
                intent=intent,
                entities=entities,
                operation="read",
                confidence=0.85,
                requires_clarification=False,
            )

        # intentهای بدون entity
        return ParsedRequest(
            intent=intent,
            entities={},
            operation="read",
            confidence=0.9,
            requires_clarification=False,
        )

    # --------------------------------------------------------
    #  intent نامفهوم
    # --------------------------------------------------------
    def _unknown(self) -> ParsedRequest:
        return ParsedRequest(
            intent="unknown",
            entities={},
            operation="read",
            confidence=0.0,
            requires_clarification=True,
            clarification_question=(
                "ای بابا ، درخواست شما را متوجه نشدم. "
                "لطفاً دقیق‌تر بفرمایید. مثلاً: "
                "«موجودی ورق فولادی در انبار مرکزی چقدر است؟»"
            ),
        )

    # --------------------------------------------------------
    #  تطبیق fuzzy با لیست‌های شناخته‌شده
    # --------------------------------------------------------
    def _match_item(self, raw: str) -> str:
        raw = (raw or "").strip()
        for item in self.KNOWN_ITEMS:
            if item in raw:
                return item
        # اگر تطبیق نبود، خود raw را برگردان
        return raw

    def _match_warehouse(self, raw: str) -> str:
        raw = (raw or "").strip()
        for wh in self.KNOWN_WAREHOUSES:
            if wh in raw:
                return wh
        return raw