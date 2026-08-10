from django.conf import settings
from django.db import models


class RequestStatusHistory(models.Model):
    service_request = models.ForeignKey(
        "cases.ServiceRequest",
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="درخواست خدمت",
    )

    from_status = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="وضعیت قبلی",
    )

    to_status = models.CharField(
        max_length=30,
        verbose_name="وضعیت جدید",
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="request_status_changes",
        verbose_name="تغییر توسط",
    )

    note = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان تغییر",
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "تاریخچه وضعیت درخواست"
        verbose_name_plural = "تاریخچه وضعیت درخواست‌ها"

    def __str__(self):
        return (
            f"{self.service_request.tracking_code}: "
            f"{self.from_status} → {self.to_status}"
        )