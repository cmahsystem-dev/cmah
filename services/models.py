from django.db import models
from django.utils.text import slugify


class ServiceCategory(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="نام دسته"
    )

    slug = models.SlugField(
    unique=True,
    blank=True,
    allow_unicode=True,
    verbose_name="آدرس"
)

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bootstrap Icon",
        verbose_name="آیکون"
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "دسته خدمت"
        verbose_name_plural = "دسته‌بندی خدمات"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Service(models.Model):
    # =====================================
    # اطلاعات اصلی
    # =====================================

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان خدمت"
    )

    slug = models.SlugField(
        unique=True,
        blank=True,
        verbose_name="آدرس (Slug)"
    )

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
        null=True,
        blank=True,
        verbose_name="دسته"
    )

    short_description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="توضیح کوتاه"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات کامل"
    )

    image = models.ImageField(
        upload_to="services/",
        blank=True,
        null=True,
        verbose_name="تصویر"
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        default="bi-file-earmark-text",
        verbose_name="Bootstrap Icon"
    )

    # =====================================
    # قیمت
    # =====================================

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
        verbose_name="درصد کش‌بک"
    )

    # =====================================
    # اطلاعات خدمت
    # =====================================

    delivery_time = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="زمان انجام"
    )

    required_documents = models.TextField(
        blank=True,
        verbose_name="مدارک موردنیاز"
    )

    steps = models.TextField(
        blank=True,
        verbose_name="مراحل انجام"
    )

    is_online = models.BooleanField(
        default=True,
        verbose_name="کاملاً آنلاین"
    )

    button_text = models.CharField(
        max_length=100,
        default="ثبت درخواست",
        verbose_name="متن دکمه"
    )

    # =====================================
    # وضعیت
    # =====================================

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="نمایش در صفحه اصلی"
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    # =====================================
    # SEO
    # =====================================

    seo_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="SEO Title"
    )

    seo_description = models.TextField(
        blank=True,
        verbose_name="SEO Description"
    )

    og_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Open Graph Title"
    )

    og_description = models.TextField(
        blank=True,
        verbose_name="Open Graph Description"
    )

    og_image = models.ImageField(
        upload_to="seo/services/",
        blank=True,
        null=True,
        verbose_name="تصویر Open Graph"
    )

    # =====================================
    # زمان
    # =====================================

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"

    @property
    def total_price(self):
        return self.government_fee + self.service_fee

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ServiceFAQ(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="faqs",
        verbose_name="خدمت"
    )

    question = models.CharField(
        max_length=255,
        verbose_name="سؤال"
    )

    answer = models.TextField(
        verbose_name="پاسخ"
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "سؤال متداول"
        verbose_name_plural = "سؤالات متداول"

    def __str__(self):
        return self.question