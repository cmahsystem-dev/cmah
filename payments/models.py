from django.conf import settings
from django.db import models

from cases.models import ServiceRequest


class PaymentMethod(models.Model):
    code = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="کد روش پرداخت",
    )

    title = models.CharField(
        max_length=100,
        verbose_name="عنوان",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="آیکون",
        help_text="مثلاً Bootstrap Icon",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="فعال",
    )

    priority = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="اولویت نمایش",
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
        ordering = [
            "priority",
            "id",
        ]
        verbose_name = "روش پرداخت"
        verbose_name_plural = "روش‌های پرداخت"

    def __str__(self):
        return self.title


class GatewayProvider(models.Model):
    code = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="کد درگاه",
    )

    title = models.CharField(
        max_length=100,
        verbose_name="عنوان",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    logo = models.ImageField(
        upload_to="payments/gateways/",
        blank=True,
        null=True,
        verbose_name="لوگو",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="فعال",
    )

    priority = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="اولویت نمایش",
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
        ordering = [
            "priority",
            "id",
        ]
        verbose_name = "ارائه‌دهنده درگاه"
        verbose_name_plural = "ارائه‌دهندگان درگاه"

    def __str__(self):
        return self.title


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"

        AWAITING_VERIFICATION = (
            "awaiting_verification",
            "در انتظار تأیید",
        )

        PAID = "paid", "پرداخت شده"
        FAILED = "failed", "ناموفق"
        CANCELLED = "cancelled", "لغو شده"

    
    

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
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="وضعیت",
    )

    method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="payments",        
        verbose_name="روش پرداخت",
    )

    gateway_provider = models.ForeignKey(
        GatewayProvider,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
        verbose_name="ارائه‌دهنده درگاه",
    )



    authority = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="شناسه تراکنش ارائه‌دهنده",
    )

    reference_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="شماره مرجع تأییدشده",
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
                fields=[
                    "service_request",
                    "status",
                ],
                name="payment_request_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.service_request.tracking_code} - "
            f"{self.amount} - "
            f"{self.get_status_display()}"
        )


class CardToCardPaymentDetail(models.Model):
    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        related_name="card_to_card_detail",
        verbose_name="پرداخت",
    )

    payer_reference = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="شماره پیگیری اعلام‌شده توسط کاربر",
    )

    receipt = models.FileField(
        upload_to="payments/card_to_card/",
        blank=True,
        null=True,
        verbose_name="رسید پرداخت",
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان اعلام پرداخت",
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verified_card_to_card_payments",
        null=True,
        blank=True,
        verbose_name="بررسی‌شده توسط",
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان بررسی",
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name="دلیل رد",
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
        verbose_name = "جزئیات پرداخت کارت‌به‌کارت"
        verbose_name_plural = "جزئیات پرداخت‌های کارت‌به‌کارت"

    def __str__(self):
        return (
            f"CardToCard - "
            f"{self.payment.service_request.tracking_code}"
        )