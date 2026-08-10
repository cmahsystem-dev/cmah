from django.db import models

from .service import Service

from django.core.exceptions import ValidationError

class ServiceField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = "text", "متن"
        TEXTAREA = "textarea", "متن چندخطی"
        NUMBER = "number", "عدد"
        DATE = "date", "تاریخ"
        SELECT = "select", "لیست انتخابی"
        RADIO = "radio", "انتخاب تکی"
        CHECKBOX = "checkbox", "چک‌باکس"
        FILE = "file", "فایل"

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="fields",
        verbose_name="خدمت",
    )

    key = models.SlugField(
        max_length=100,
        verbose_name="شناسه فیلد",
    )

    label = models.CharField(
        max_length=150,
        verbose_name="عنوان فیلد",
    )

    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT,
        verbose_name="نوع فیلد",
    )

    required = models.BooleanField(
        default=False,
        verbose_name="الزامی",
    )

    reusable = models.BooleanField(
        default=False,
        verbose_name="قابل استفاده مجدد",
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )

    help_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="راهنما",
    )

    placeholder = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Placeholder",
    )

    choices = models.JSONField(
        default=list,
        blank=True,
        verbose_name="گزینه‌ها",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="فعال",
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
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "key"],
                name="unique_service_field_key",
            )
        ]
        verbose_name = "فیلد خدمت"
        verbose_name_plural = "فیلدهای خدمات"


    def clean(self):
        super().clean()

        choice_types = {
            self.FieldType.SELECT,
            self.FieldType.RADIO,
        }

        if self.field_type in choice_types and not self.choices:
            raise ValidationError({
                "choices": "برای این نوع فیلد حداقل یک گزینه الزامی است."
            })

        if self.field_type not in choice_types and self.choices:
            raise ValidationError({
                "choices": "این نوع فیلد نباید دارای گزینه باشد."
            })

        if self.field_type == self.FieldType.FILE and self.reusable:
            raise ValidationError({
                "reusable": "فیلد فایل نمی‌تواند قابل استفاده مجدد باشد."
            })
    def __str__(self):
        return f"{self.service} - {self.label}"