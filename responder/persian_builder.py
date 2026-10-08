# ============================================================
#  ZSolution - Persian Responder
#  تبدیل QueryResult به پاسخ فارسی طبیعی
# ============================================================

from core.models import NaturalResponse, ParsedRequest, QueryResult


class PersianResponder:
    """ساخت پاسخ نهایی به فارسی بر اساس intent و نتیجهٔ دیتابیس."""

    # --------------------------------------------------------
    #  API عمومی
    # --------------------------------------------------------
    def build(self, result: QueryResult, request: ParsedRequest) -> NaturalResponse:
        """QueryResult + ParsedRequest → NaturalResponse."""

        # خطای اجرای کوئری
        if result.status == "error":
            return NaturalResponse(
                text="متأسفانه در اجرای درخواست خطایی رخ داد.",
                is_empty=False,
                error=result.error,
            )

        # نتیجهٔ خالی
        if result.status == "empty" or result.row_count == 0:
            return NaturalResponse(
                text=self._empty_message(request),
                is_empty=True,
            )

        # بر اساس intent
        if request.intent == "inventory_query":
            return self._inventory_response(result)

        if request.intent == "item_list":
            return self._list_response(result, "کالا")

        if request.intent == "warehouse_list":
            return self._list_response(result, "انبار")

        # intentهای بدون دیتابیس
        if request.intent == "greeting":
            return NaturalResponse(
                text="سلام! چطور می‌توانم کمک کنم؟",
                is_empty=False,
            )

        if request.intent == "thanks":
            return NaturalResponse(
                text="خواهش می‌کنم. سؤال دیگری دارید؟",
                is_empty=False,
            )

        if request.intent == "goodbye":
            return NaturalResponse(
                text="خداحافظ! روز خوبی داشته باشید.",
                is_empty=False,
            )

        # fallback
        return NaturalResponse(
            text="پاسخ شما آماده است.",
            is_empty=False,
        )

    # --------------------------------------------------------
    #  پاسخ برای استعلام موجودی
    # --------------------------------------------------------
    def _inventory_response(self, result: QueryResult) -> NaturalResponse:
        row = result.rows[0]
        c = result.columns

        item_name   = row[c.index("item_name")]
        warehouse   = row[c.index("warehouse_name")]
        quantity    = row[c.index("quantity")]
        unit        = row[c.index("unit")]

        qty_fa = self._to_persian_digits(str(quantity))

        text = (
            f"موجودی {item_name} در {warehouse} "
            f"برابر {qty_fa} {unit} است."
        )
        return NaturalResponse(text=text, is_empty=False)

    # --------------------------------------------------------
    #  پاسخ برای لیست (کالا یا انبار)
    # --------------------------------------------------------
    def _list_response(self, result: QueryResult, label: str) -> NaturalResponse:
        count = result.row_count
        count_fa = self._to_persian_digits(str(count))

        # نام‌ها را استخراج کن (اولین ستون)
        names = [row[0] for row in result.rows]

        if count <= 5:
            names_text = "، ".join(names[:-1])
            if count > 1:
                names_text += " و " + names[-1]
            text = f"{count_fa} {label} در سیستم ثبت شده است: {names_text}."
        else:
            text = (
                f"{count_fa} {label} در سیستم ثبت شده است. "
                f"به‌عنوان مثال: {names[0]}، {names[1]} و ..."
            )

        return NaturalResponse(text=text, is_empty=False)

    # --------------------------------------------------------
    #  پیام خالی بودن نتیجه
    # --------------------------------------------------------
    def _empty_message(self, request: ParsedRequest) -> str:
        if request.intent == "inventory_query":
            item = request.entities.get("item_name", "کالای موردنظر")
            wh   = request.entities.get("warehouse_name", "انبار موردنظر")
            return (
                f"متأسفانه اطلاعاتی برای {item} در {wh} پیدا نشد. "
                f"لطفاً از صحت نام کالا و انبار مطمئن شوید."
            )
        return "رکوردی مطابق درخواست شما پیدا نشد."

    # --------------------------------------------------------
    #  تبدیل ارقام به فارسی
    # --------------------------------------------------------
    def _to_persian_digits(self, s: str) -> str:
        table = str.maketrans("0123456789,", "۰۱۲۳۴۵۶۷۸۹٬")
        return str(s).translate(table)