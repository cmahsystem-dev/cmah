from payments.models import PaymentMethod


class PaymentAvailabilityService:
    """
    مشخص می‌کند کدام روش‌های پرداخت واقعاً
    توسط Backend قابل استفاده هستند.

    فعال بودن رکورد در Admin به‌تنهایی
    به معنی قابل استفاده بودن Method نیست.
    """

    SUPPORTED_METHODS = {
        "card_to_card",
    }

    @classmethod
    def is_backend_supported(
        cls,
        *,
        method_code: str,
    ) -> bool:
        return method_code in cls.SUPPORTED_METHODS

    @classmethod
    def get_available_methods(cls):
        return (
            PaymentMethod.objects
            .filter(
                is_active=True,
                code__in=cls.SUPPORTED_METHODS,
            )
            .order_by(
                "priority",
                "id",
            )
        )

    @classmethod
    def is_available(
        cls,
        *,
        method: PaymentMethod,
    ) -> bool:
        return (
            method.is_active
            and cls.is_backend_supported(
                method_code=method.code,
            )
        )
    