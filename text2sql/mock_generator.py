# ============================================================
#  ZSolution - Mock Text-to-SQL
#  تولید SQL برای intentهای پشتیبانی‌شده — بدون LLM
# ============================================================

from core.models import ParsedRequest, SQLQuery


class MockTextToSQL:
    """تولید کوئری SQL با template — فقط برای تست زنجیره."""

    # --------------------------------------------------------
    #  شِمای آزمایشی (فقط برای مستندسازی)
    # --------------------------------------------------------
    SCHEMA = {
        "items":      ["id", "name", "unit"],
        "warehouses": ["id", "name", "location"],
        "inventory":  ["id", "item_id", "warehouse_id", "quantity"],
    }

    # --------------------------------------------------------
    #  قالب‌های SQL برای هر intent
    # --------------------------------------------------------
    TEMPLATES = {
        "inventory_query": (
            "SELECT i.name AS item_name, "
            "       w.name AS warehouse_name, "
            "       inv.quantity AS quantity, "
            "       i.unit AS unit "
            "FROM inventory inv "
            "JOIN items i ON i.id = inv.item_id "
            "JOIN warehouses w ON w.id = inv.warehouse_id "
            "WHERE i.name = :item AND w.name = :warehouse"
        ),
        "item_list": (
            "SELECT name, unit FROM items ORDER BY name"
        ),
        "warehouse_list": (
            "SELECT name, location FROM warehouses ORDER BY name"
        ),
    }

    # --------------------------------------------------------
    #  API عمومی
    # --------------------------------------------------------
    def generate(self, request: ParsedRequest) -> SQLQuery:
        """ParsedRequest → SQLQuery."""
        intent = request.intent

        if intent not in self.TEMPLATES:
            return SQLQuery(
                sql="",
                params={},
                operation="read",
                explanation=f"intent «{intent}» پشتیبانی نمی‌شود.",
                valid=False,
            )

        sql = self.TEMPLATES[intent]
        params = {}

        if intent == "inventory_query":
            item      = request.entities.get("item_name", "").strip()
            warehouse = request.entities.get("warehouse_name", "").strip()

            if not item or not warehouse:
                return SQLQuery(
                    sql="",
                    params={},
                    operation="read",
                    explanation=(
                        "برای استعلام موجودی، نام کالا و نام انبار "
                        "هر دو لازم است."
                    ),
                    valid=False,
                )

            params = {"item": item, "warehouse": warehouse}

        return SQLQuery(
            sql=sql,
            params=params,
            operation="read",
            explanation=f"کوئری Mock برای intent={intent}",
            valid=True,
        )