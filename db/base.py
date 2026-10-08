# ============================================================
#  ZSolution - Database Adapter Interface
#  رابط انتزاعی برای لایهٔ دسترسی به داده
# ============================================================

from abc import ABC, abstractmethod

from core.models import QueryResult


class BaseDatabaseAdapter(ABC):
    """رابط پایه برای همهٔ آداپتورهای دیتابیس."""

    @abstractmethod
    def execute(self, sql: str, params: dict, intent: str) -> QueryResult:
        """
        کوئری را اجرا می‌کند و QueryResult برمی‌گرداند.

        Args:
            sql: کوئری SQL (اعتبارسنجی‌شده)
            params: پارامترهای کوئری
            intent: intent کاربر (برای آداپتور Mock مفید است)

        Returns:
            QueryResult
        """
        raise NotImplementedError