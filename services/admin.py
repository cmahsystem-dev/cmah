from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ServiceCategory,
    Service,
    ServiceFAQ,
)


# =====================================================
# FAQ Inline
# =====================================================

class ServiceFAQInline(admin.TabularInline):
    model = ServiceFAQ
    extra = 1

    fields = (
        "question",
        "answer",
        "sort_order",
        "is_active",
    )


# =====================================================
# Category Admin
# =====================================================

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "sort_order",
        "is_active",
    )

    list_display_links = (
        "name",
    )

    list_editable = (
        "sort_order",
        "is_active",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "sort_order",
        "name",
    )


# =====================================================
# Service Admin
# =====================================================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):

    inlines = [
        ServiceFAQInline,
    ]

    list_display = (
        "title",
        "image_preview",
        "category",
        "total_price",
        "delivery_time",
        "faq_count",
        "is_featured",
        "is_active",
    )

    list_display_links = (
        "title",
    )

    list_filter = (
        "category",
        "is_active",
        "is_featured",
        "is_online",
    )

    search_fields = (
        "title",
        "short_description",
        "description",
        "slug",
    )

    ordering = (
        "sort_order",
        "title",
    )

    list_editable = (
        "is_featured",
        "is_active",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "image_preview_large",
    )

    fieldsets = (

        (
            "اطلاعات اصلی",
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "short_description",
                    "description",
                )
            },
        ),

        (
            "تصویر",
            {
                "fields": (
                    "image",
                    "image_preview_large",
                    "icon",
                )
            },
        ),

        (
            "قیمت",
            {
                "fields": (
                    "government_fee",
                    "service_fee",
                    "cashback_percent",
                )
            },
        ),

        (
            "اطلاعات خدمت",
            {
                "fields": (
                    "delivery_time",
                    "required_documents",
                    "steps",
                    "is_online",
                    "button_text",
                )
            },
        ),

        (
            "وضعیت نمایش",
            {
                "fields": (
                    "is_active",
                    "is_featured",
                    "sort_order",
                )
            },
        ),

        (
            "SEO",
            {
                "classes": ("collapse",),
                "fields": (
                    "seo_title",
                    "seo_description",
                    "og_title",
                    "og_description",
                    "og_image",
                )
            },
        ),

        (
            "اطلاعات سیستم",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),

    )

    @admin.display(description="تصویر")
    def image_preview(self, obj):

        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius:8px;object-fit:cover;">',
                obj.image.url
            )

        return "-"

    @admin.display(description="پیش‌نمایش تصویر")
    def image_preview_large(self, obj):

        if obj.image:
            return format_html(
                '<img src="{}" width="250" style="border-radius:10px;">',
                obj.image.url
            )

        return "تصویری ثبت نشده است."

    @admin.display(description="تعداد سوالات")
    def faq_count(self, obj):
        return obj.faqs.count()


# =====================================================
# FAQ Admin
# =====================================================

@admin.register(ServiceFAQ)
class ServiceFAQAdmin(admin.ModelAdmin):

    list_display = (
        "question",
        "service",
        "sort_order",
        "is_active",
    )

    list_display_links = (
        "question",
    )

    list_filter = (
        "service",
        "is_active",
    )

    list_editable = (
        "sort_order",
        "is_active",
    )

    search_fields = (
        "question",
        "answer",
    )

    ordering = (
        "service",
        "sort_order",
    )