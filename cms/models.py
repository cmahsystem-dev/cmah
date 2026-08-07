from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class SiteSetting(models.Model):
    # -------------------------
    # اطلاعات اصلی
    # -------------------------
    site_name = models.CharField(
        max_length=150,
        verbose_name="نام سایت",
    )

    slogan = models.CharField(
        max_length=255,
        verbose_name="شعار سایت",
    )

    site_description = models.TextField(
        blank=True,
        verbose_name="توضیحات سایت",
    )

    logo = models.ImageField(
        upload_to="site/",
        blank=True,
        null=True,
        verbose_name="لوگو",
    )

    favicon = models.ImageField(
        upload_to="site/",
        blank=True,
        null=True,
        verbose_name="فاوآیکون",
    )

    # -------------------------
    # اطلاعات تماس
    # -------------------------
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="شماره تماس",
    )

    email = models.EmailField(
        blank=True,
        verbose_name="ایمیل",
    )

    whatsapp = models.URLField(
        blank=True,
        verbose_name="لینک واتساپ",
    )

    address = models.TextField(
        blank=True,
        verbose_name="آدرس",
    )

    # -------------------------
    # شبکه‌های اجتماعی
    # -------------------------
    telegram = models.URLField(
        blank=True,
        verbose_name="تلگرام",
    )

    instagram = models.URLField(
        blank=True,
        verbose_name="اینستاگرام",
    )

    linkedin = models.URLField(
        blank=True,
        verbose_name="لینکدین",
    )

    aparat = models.URLField(
        blank=True,
        verbose_name="آپارات",
    )

    # -------------------------
    # فوتر
    # -------------------------
    footer_text = models.TextField(
        blank=True,
        verbose_name="متن فوتر",
    )

    copyright = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="متن کپی‌رایت",
    )

    # -------------------------
    # SEO
    # -------------------------
    seo_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="عنوان سئو",
    )

    seo_description = models.TextField(
        blank=True,
        verbose_name="توضیحات سئو",
    )

    google_site_verification = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Google Search Console Verification",
    )

    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Google Analytics ID",
    )

    default_og_image = models.ImageField(
        upload_to="seo/",
        blank=True,
        null=True,
        verbose_name="تصویر پیش‌فرض Open Graph",
    )

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.site_name


class HomePageSetting(models.Model):
    search_title = models.CharField(
        max_length=150,
        default="چه خدمتی نیاز دارید؟",
        verbose_name="عنوان جستجو",
    )

    search_placeholder = models.CharField(
        max_length=255,
        default="نام خدمت موردنظر را جستجو کنید",
        verbose_name="متن داخل جستجو",
    )

    search_button_text = models.CharField(
        max_length=100,
        default="جستجو",
        verbose_name="متن دکمه جستجو",
    )

    featured_services_title = models.CharField(
        max_length=150,
        default="خدمات پرکاربرد",
        verbose_name="عنوان خدمات پرکاربرد",
    )

    featured_services_button_text = models.CharField(
        max_length=100,
        default="مشاهده همه خدمات",
        verbose_name="متن دکمه همه خدمات",
    )

    process_title = models.CharField(
        max_length=150,
        default="چطور کار می‌کند؟",
        verbose_name="عنوان مراحل انجام کار",
    )

    features_title = models.CharField(
        max_length=150,
        default="چرا CMAH؟",
        verbose_name="عنوان بخش مزیت‌ها",
    )

    cta_title = models.CharField(
        max_length=200,
        default="همین حالا درخواست خود را ثبت کنید",
        verbose_name="عنوان دعوت به اقدام",
    )

    cta_description = models.TextField(
        default="خدمت موردنظر خود را انتخاب کنید و درخواستتان را آنلاین ثبت کنید.",
        verbose_name="توضیحات دعوت به اقدام",
    )

    cta_button_text = models.CharField(
        max_length=100,
        default="مشاهده خدمات",
        verbose_name="متن دکمه دعوت به اقدام",
    )

    class Meta:
        verbose_name = "تنظیمات صفحه اصلی"
        verbose_name_plural = "تنظیمات صفحه اصلی"

    def __str__(self):
        return "تنظیمات صفحه اصلی"


class HeroSection(models.Model):
    badge_text = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="متن بالای عنوان",
    )

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان اصلی",
    )

    subtitle = models.TextField(
        verbose_name="توضیحات زیر عنوان",
    )

    primary_button_text = models.CharField(
        max_length=100,
        verbose_name="متن دکمه اصلی",
    )

    primary_button_url = models.CharField(
        max_length=255,
        verbose_name="لینک دکمه اصلی",
        help_text="مثال: /services/",
    )

    secondary_button_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="متن دکمه دوم",
    )

    secondary_button_url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="لینک دکمه دوم",
        help_text="مثال: #how-it-works",
    )

    image = models.ImageField(
        upload_to="hero/",
        blank=True,
        null=True,
        verbose_name="تصویر",
    )

    image_alt = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="متن جایگزین تصویر",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "بخش Hero"
        verbose_name_plural = "بخش‌های Hero"

    def __str__(self):
        return self.title


class TrustItem(models.Model):
    title = models.CharField(
        max_length=100,
        verbose_name="عنوان",
    )

    icon = models.CharField(
        max_length=100,
        default="bi-check-circle",
        verbose_name="آیکون Bootstrap",
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "نشان اعتماد"
        verbose_name_plural = "نشان‌های اعتماد"

    def __str__(self):
        return self.title


class ProcessStep(models.Model):
    title = models.CharField(
        max_length=150,
        verbose_name="عنوان مرحله",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات مرحله",
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="آیکون Bootstrap",
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "مرحله انجام کار"
        verbose_name_plural = "مراحل انجام کار"

    def __str__(self):
        return self.title


class Statistic(models.Model):
    title = models.CharField(
        max_length=100,
        verbose_name="عنوان",
    )

    value = models.CharField(
        max_length=50,
        verbose_name="مقدار",
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="آیکون Bootstrap",
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "آمار"
        verbose_name_plural = "آمارها"

    def __str__(self):
        return self.title


class Feature(models.Model):
    title = models.CharField(
        max_length=150,
        verbose_name="عنوان",
    )

    description = models.TextField(
        verbose_name="توضیحات",
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="آیکون Bootstrap",
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "مزیت"
        verbose_name_plural = "مزیت‌ها"

    def __str__(self):
        return self.title

    from django.db import models


class Menu(models.Model):
    LOCATION_CHOICES = (
        ("header", "Header"),
        ("footer", "Footer"),
    )

    name = models.CharField(
        max_length=100,
        verbose_name="نام منو"
    )
    slug = models.SlugField(
    max_length=50,
    unique=True,
    verbose_name="شناسه"
)

    location = models.CharField(
        max_length=20,
        choices=LOCATION_CHOICES,
        default="header",
        verbose_name="محل نمایش"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )


    class Meta:
        verbose_name = "منو"
        verbose_name_plural = "منوها"


    def __str__(self):
        return self.name



class MenuItem(models.Model):

    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="منو"
    )

    title = models.CharField(
        max_length=100,
        verbose_name="عنوان"
    )

    url = models.CharField(
        max_length=255,
        verbose_name="لینک"
    )

    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="ترتیب نمایش"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    target = models.CharField(
        max_length=50,
        default="_self",
        verbose_name="Target"
    )


    class Meta:
        ordering = ["order"]
        verbose_name = "آیتم منو"
        verbose_name_plural = "آیتم‌های منو"


    def __str__(self):
        return self.title

    
class Page(models.Model):

    STATUS_CHOICES = (
        ("draft", "پیش‌نویس"),
        ("published", "منتشر شده"),
        ("archived", "بایگانی"),
    )


    TEMPLATE_CHOICES = (
        ("default", "پیش فرض"),
        ("contact", "تماس با ما"),
        ("faq", "سوالات متداول"),
    )


    title = models.CharField(
        max_length=200,
        verbose_name="عنوان صفحه"
    )


    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="شناسه صفحه"
    )


    content = CKEditor5Field(
    config_name="extends",
    verbose_name="محتوا"
    )


    excerpt = models.TextField(
        blank=True,
        verbose_name="خلاصه"
    )


    template = models.CharField(
        max_length=50,
        choices=TEMPLATE_CHOICES,
        default="default",
        verbose_name="قالب نمایش"
    )


    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name="وضعیت"
    )


    seo_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="عنوان سئو"
    )


    seo_description = models.TextField(
        blank=True,
        verbose_name="توضیحات سئو"
    )


    og_image = models.ImageField(
        upload_to="seo/pages/",
        blank=True,
        null=True,
        verbose_name="تصویر Open Graph"
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )


    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین تغییر"
    )


    class Meta:
        ordering = ["title"]
        verbose_name = "صفحه"
        verbose_name_plural = "صفحات"


    def __str__(self):
        return self.title

class FAQ(models.Model):

    question = models.CharField(
        max_length=255,
        verbose_name="سوال"
    )

    answer = models.TextField(
        verbose_name="پاسخ"
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )


    class Meta:
        ordering = [
            "order"
        ]

        verbose_name = "سوال متداول"
        verbose_name_plural = "سوالات متداول"


    def __str__(self):
        return self.question    