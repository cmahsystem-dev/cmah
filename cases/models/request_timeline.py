from django.conf import settings
from django.db import models


class RequestTimeline(models.Model):
    class EventType(models.TextChoices):
        STATUS_CHANGED = "status_changed", "تغییر وضعیت"
        DOCUMENT_UPLOADED = "document_uploaded", "بارگذاری مدرک"
        DOCUMENT_APPROVED = "document_approved", "تأیید مدرک"
        DOCUMENT_REJECTED = "document_rejected", "رد مدرک"
        PAYMENT = "payment", "پرداخت"
        NOTE = "note", "یادداشت"
        SYSTEM = "system", "سیستمی"

    service_request = models.ForeignKey(
        "cases.ServiceRequest",
        on_delete=models.CASCADE,
        related_name="timeline",
        verbose_name="درخواست خدمت",
    )

    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        db_index=True,
        verbose_name="نوع رویداد",
    )

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="request_timeline_events",
        verbose_name="انجام‌دهنده",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="اطلاعات تکمیلی",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="زمان رویداد",
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "رویداد درخواست"
        verbose_name_plural = "رویدادهای درخواست‌ها"

    def __str__(self):
        return (
            f"{self.service_request.tracking_code} - "
            f"{self.get_event_type_display()} - "
            f"{self.title}"
        )