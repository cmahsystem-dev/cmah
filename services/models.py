from django.db import models
from django.utils.text import slugify


class Service(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان خدمت"
    )

    slug = models.SlugField(
        unique=True,
        blank=True,
        verbose_name="آدرس خدمت"
    )

    short_description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="توضیح کوتاه"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    government_fee = models.PositiveIntegerField(
        default=0,
        verbose_name="هزینه دولتی"
    )

    service_fee = models.PositiveIntegerField(
        default=0,
        verbose_name="کارمزد CMAH"
    )

    cashback_percent = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="درصد کش بک"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title