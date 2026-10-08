# ============================================================
#  ZSolution - Mock Database Adapter
#  پاسخ‌های از پیش تعریف‌شده — بدون دیتابیس واقعی
# ============================================================

from core.models import QueryResult
from db.base import BaseDatabaseAdapter


class MockDatabaseAdapter(BaseDatabaseAdapter):
    """شبیه‌ساز دیتابیس — داده‌های آزمایشی."""

    # --------------------------------------------------------
    #  داده‌های آزمایشی
    # --------------------------------------------------------
    MOCK_DATA = {
        "inventory_query": {
            ("ورق فولادی", "انبار مرکزی"): [
                {
                    "item_name": "ورق فولادی",
                    "warehouse_name": "انبار مرکزی",
                    "quantity": 1200,
                    "unit": "کیلوگرم",
                },
            ],
            ("میلگرد", "انبار شمال"): [
                {
                    "item_name": "میلگرد",
                    "warehouse_name": "انبار شمال",
                    "quantity": 800,
                    "unit": "کیلوگرم",
                },
            ],
        },
        "item_list": [
            {"name": "ورق فولادی", "unit": "کیلوگرم"},
            {"name": "میلگرد",      "unit": "کیلوگرم"},
            {"name": "تیرآهن",      "unit": "شاخه"},
            {"name": "لوله",        "unit": "شاخه"},
            {"name": "پروفیل",      "unit": "شاخه"},
        ],
        "warehouse_list": [
            {"name": "انبار مرکزی", "location": "تهران"},
            {"name": "انبار شمال",  "location": "رشت"},
            {"name": "انبار جنوب",  "location": "اهواز"},
        ],
    }

    # --------------------------------------------------------
    #  API عمومی
    # --------------------------------------------------------
    def execute(self, sql: str, params: dict, intent: str) -> QueryResult:
        """اجرای Mock بر اساس intent و پارامترها."""

        try:
            if intent == "inventory_query":
                data = self._inventory_data(params)
            elif intent == "item_list":
                data = self.MOCK_DATA["item_list"]
            elif intent == "warehouse_list":
                data = self.MOCK_DATA["warehouse_list"]
            else:
                return QueryResult(
                    status="empty",
                    columns=[],
                    rows=[],
                    row_count=0,
                    is_mock=True,
                )

            if not data:
                return QueryResult(
                    status="empty",
                    columns=[],
                    rows=[],
                    row_count=0,
                    is_mock=True,
                )

            columns = list(data[0].keys())
            rows = [list(row.values()) for row in data]

            return QueryResult(
                status="ok",
                columns=columns,
                rows=rows,
                row_count=len(rows),
                is_mock=True,
            )

        except Exception as e:
            return QueryResult(
                status="error",
                columns=[],
                rows=[],
                row_count=0,
                error=str(e),
                is_mock=True,
            )

    # --------------------------------------------------------
    #  جست‌وجوی دادهٔ موجودی
    # --------------------------------------------------------
    def _inventory_data(self, params: dict) -> list:
        item = (params.get("item") or "").strip()
        warehouse = (params.get("warehouse") or "").strip()

        if not item or not warehouse:
            return []

        # جست‌وجوی دقیق
        key = (item, warehouse)
        if key in self.MOCK_DATA["inventory_query"]:
            return self.MOCK_DATA["inventory_query"][key]

        # جست‌وجوی fuzzy: اگر نام دقیق نبود، دنبال تطبیق جزئی
        for (it, wh), data in self.MOCK_DATA["inventory_query"].items():
            if (item in it or it in item) and (warehouse in wh or wh in warehouse):
                return data

        return []