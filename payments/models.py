from django.db import models

from cases.models import ServiceRequest


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        PAID = "paid", "پرداخت شده"
        FAILED = "failed", "ناموفق"
        CANCELLED = "cancelled", "لغو شده"

    class Gateway(models.TextChoices):
        MANUAL = "manual", "دستی"
        ZARINPAL = "zarinpal", "زرین‌پال"
        IDPAY = "idpay", "آیدی‌پی"

    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="درخواست خدمت",
    )

    amount = models.PositiveBigIntegerField(
        verbose_name="مبلغ",
        help_text="مبلغ به ریال",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="وضعیت",
    )

    gateway = models.CharField(
        max_length=30,
        choices=Gateway.choices,
        default=Gateway.MANUAL,
        verbose_name="درگاه پرداخت",
    )

    authority = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="شناسه پرداخت در درگاه",
    )

    reference_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="شماره مرجع",
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان پرداخت",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        indexes = [
            models.Index(
                fields=["service_request", "status"],
                name="payment_request_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.service_request.tracking_code} - "
            f"{self.amount} - "
            f"{self.get_status_display()}"
        )