from django.conf import settings
from django.db import models


def request_document_upload_to(instance, filename):
    return (
        f"cases/{instance.service_request.tracking_code}/"
        f"{instance.field_key}/v{instance.version}/{filename}"
    )


class RequestDocument(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار بررسی"
        APPROVED = "approved", "تأیید شده"
        REJECTED = "rejected", "رد شده"
        REPLACED = "replaced", "جایگزین شده"

    service_request = models.ForeignKey(
        "cases.ServiceRequest",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="درخواست خدمت",
    )

    field_key = models.SlugField(
        max_length=100,
        verbose_name="شناسه فیلد",
    )

    file = models.FileField(
        upload_to=request_document_upload_to,
        verbose_name="فایل",
    )

    version = models.PositiveIntegerField(
        default=1,
        verbose_name="نسخه",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="وضعیت",
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name="دلیل رد",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_request_documents",
        verbose_name="آپلود توسط",
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
        ordering = ["field_key", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "service_request",
                    "field_key",
                    "version",
                ],
                name="unique_request_document_version",
            )
        ]
        verbose_name = "مدرک درخواست"
        verbose_name_plural = "مدارک درخواست‌ها"

    def __str__(self):
        return (
            f"{self.service_request.tracking_code} - "
            f"{self.field_key} - v{self.version}"
        )