import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from services.models import Service



def generate_tracking_code():
    return f"CM-{secrets.token_hex(4).upper()}"


class ServiceRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        SUBMITTED = "submitted", "ثبت شده"
        UNDER_REVIEW = "under_review", "در حال بررسی"
        NEEDS_CORRECTION = "needs_correction", "نیازمند اصلاح"
        READY_FOR_PAYMENT = "ready_for_payment", "آماده پرداخت"
        PROCESSING = "processing", "در حال انجام"
        COMPLETED = "completed", "تکمیل شده"
        CANCELLED = "cancelled", "لغو شده"
        REJECTED = "rejected", "رد شده"

    ALLOWED_TRANSITIONS = {
        Status.DRAFT: {
            Status.SUBMITTED,
            Status.CANCELLED,
        },
        Status.SUBMITTED: {
            Status.UNDER_REVIEW,
            Status.CANCELLED,
        },
        Status.UNDER_REVIEW: {
            Status.NEEDS_CORRECTION,
            Status.READY_FOR_PAYMENT,
            Status.REJECTED,
        },
        Status.NEEDS_CORRECTION: {
            Status.SUBMITTED,
            Status.CANCELLED,
        },
        Status.READY_FOR_PAYMENT: {
            Status.PROCESSING,
            Status.CANCELLED,
        },
        Status.PROCESSING: {
            Status.COMPLETED,
            Status.CANCELLED,
        },
        Status.COMPLETED: set(),
        Status.CANCELLED: set(),
        Status.REJECTED: set(),
    }

    tracking_code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        default=generate_tracking_code,
        editable=False,
        verbose_name="کد پیگیری",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="service_requests",
        verbose_name="کاربر",
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="service_requests",
        verbose_name="خدمت",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name="وضعیت",
    )

    request_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="اطلاعات درخواست",
    )

    amount = models.PositiveBigIntegerField(
        default=0,
        verbose_name="مبلغ",
        help_text="مبلغ به ریال",
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان ثبت",
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان شروع انجام",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان تکمیل",
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
        verbose_name = "درخواست خدمت"
        verbose_name_plural = "درخواست‌های خدمات"

    def can_transition_to(self, new_status: str) -> bool:
        allowed_statuses = self.ALLOWED_TRANSITIONS.get(
            self.status,
            set(),
    )

        return new_status in allowed_statuses

    @transaction.atomic
    def transition_to(
        self,
        new_status: str,
        changed_by=None,
        note: str = "",
    ) -> None:
        if new_status not in self.Status.values:
            raise ValidationError("وضعیت درخواست نامعتبر است.")

        if not self.can_transition_to(new_status):
            raise ValidationError(
                f"تغییر وضعیت از "
                f"{self.get_status_display()} "
                f"به {self.Status(new_status).label} "
                f"مجاز نیست."
            )

        previous_status = self.status

        self.status = new_status
        update_fields = ["status", "updated_at"]

        if (
            new_status == self.Status.SUBMITTED
            and self.submitted_at is None
        ):
            self.submitted_at = timezone.now()
            update_fields.append("submitted_at")

        elif (
            new_status == self.Status.PROCESSING
            and self.started_at is None
        ):
            self.started_at = timezone.now()
            update_fields.append("started_at")

        elif (
            new_status == self.Status.COMPLETED
            and self.completed_at is None
        ):
            self.completed_at = timezone.now()
            update_fields.append("completed_at")

        self.save(update_fields=update_fields)

        from cases.models import RequestStatusHistory

        RequestStatusHistory.objects.create(
            service_request=self,
            from_status=previous_status,
            to_status=new_status,
            changed_by=changed_by,
            note=note,
        )


        from cases.services.request_timeline_service import RequestTimelineService

        RequestTimelineService.record(
            service_request=self,
            event_type="status_changed",
            title=f"وضعیت درخواست به «{self.get_status_display()}» تغییر کرد.",
            actor=changed_by,
            metadata={
                "from_status": previous_status,
                "to_status": new_status,
            },
        )

    def __str__(self):
        return f"{self.tracking_code} - {self.service}"