from django.contrib import admin

from .models import (
    Feature,
    HeroSection,
    HomePageSetting,
    ProcessStep,
    SiteSetting,
    Statistic,
    TrustItem,
    Menu,
    MenuItem,
    Page,
    FAQ,
)


class SingletonAdminMixin:
    """اجازه ایجاد فقط یک رکورد برای تنظیمات سراسری."""

    def has_add_permission(self, request):
        return not self.model.objects.exists()


@admin.register(SiteSetting)
class SiteSettingAdmin(SingletonAdminMixin, admin.ModelAdmin):
    list_display = (
        "site_name",
        "phone",
        "email",
    )

    list_display_links = (
        "site_name",
    )

    fieldsets = (
        (
            "اطلاعات اصلی",
            {
                "fields": (
                    "site_name",
                    "slogan",
                    "site_description",
                    "logo",
                    "favicon",
                ),
            },
        ),
        (
            "اطلاعات تماس",
            {
                "fields": (
                    "phone",
                    "email",
                    "whatsapp",
                    "address",
                ),
            },
        ),
        (
            "شبکه‌های اجتماعی",
            {
                "fields": (
                    "telegram",
                    "instagram",
                    "linkedin",
                    "aparat",
                ),
            },
        ),
        (
            "فوتر",
            {
                "fields": (
                    "footer_text",
                    "copyright",
                ),
            },
        ),
        (
            "سئو و ابزارهای گوگل",
            {
                "fields": (
                    "seo_title",
                    "seo_description",
                    "default_og_image",
                    "google_site_verification",
                    "google_analytics_id",
                ),
            },
        ),
    )


@admin.register(HomePageSetting)
class HomePageSettingAdmin(SingletonAdminMixin, admin.ModelAdmin):
    list_display = (
        "__str__",
    )

    list_display_links = (
        "__str__",
    )

    fieldsets = (
        (
            "جستجوی خدمات",
            {
                "fields": (
                    "search_title",
                    "search_placeholder",
                    "search_button_text",
                ),
            },
        ),
        (
            "عنوان بخش‌ها",
            {
                "fields": (
                    "featured_services_title",
                    "featured_services_button_text",
                    "process_title",
                    "features_title",
                ),
            },
        ),
        (
            "دعوت به اقدام پایانی",
            {
                "fields": (
                    "cta_title",
                    "cta_description",
                    "cta_button_text",
                ),
            },
        ),
    )


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "sort_order",
        "is_active",
    )

    list_display_links = (
        "title",
    )

    list_editable = (
        "sort_order",
        "is_active",
    )

    search_fields = (
        "title",
        "subtitle",
        "badge_text",
    )

    ordering = (
        "sort_order",
        "id",
    )

    fieldsets = (
        (
            "محتوا",
            {
                "fields": (
                    "badge_text",
                    "title",
                    "subtitle",
                ),
            },
        ),
        (
            "دکمه‌ها",
            {
                "fields": (
                    "primary_button_text",
                    "primary_button_url",
                    "secondary_button_text",
                    "secondary_button_url",
                ),
            },
        ),
        (
            "تصویر",
            {
                "fields": (
                    "image",
                    "image_alt",
                ),
            },
        ),
        (
            "وضعیت نمایش",
            {
                "fields": (
                    "sort_order",
                    "is_active",
                ),
            },
        ),
    )


@admin.register(TrustItem)
class TrustItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "icon",
        "sort_order",
        "is_active",
    )

    list_display_links = (
        "title",
    )

    list_editable = (
        "sort_order",
        "is_active",
    )

    search_fields = (
        "title",
        "icon",
    )

    ordering = (
        "sort_order",
        "id",
    )

    fields = (
        "title",
        "icon",
        "sort_order",
        "is_active",
    )


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "description_preview",
        "icon",
        "sort_order",
        "is_active",
    )

    # عنوان مرحله، لینک ورود به صفحه ویرایش است.
    list_display_links = (
        "title",
    )

    # این دو فیلد مستقیماً از صفحه لیست هم قابل تغییر هستند.
    list_editable = (
        "sort_order",
        "is_active",
    )

    search_fields = (
        "title",
        "description",
        "icon",
    )

    ordering = (
        "sort_order",
        "id",
    )

    fieldsets = (
        (
            "اطلاعات مرحله",
            {
                "fields": (
                    "title",
                    "description",
                    "icon",
                ),
            },
        ),
        (
            "وضعیت نمایش",
            {
                "fields": (
                    "sort_order",
                    "is_active",
                ),
            },
        ),
    )

    @admin.display(description="توضیحات")
    def description_preview(self, obj):
        if not obj.description:
            return "—"

        if len(obj.description) <= 60:
            return obj.description

        return f"{obj.description[:60]}..."


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "value",
        "icon",
        "sort_order",
        "is_active",
    )

    list_display_links = (
        "title",
    )

    list_editable = (
        "sort_order",
        "is_active",
    )

    search_fields = (
        "title",
        "value",
    )

    ordering = (
        "sort_order",
        "id",
    )

    fields = (
        "title",
        "value",
        "icon",
        "sort_order",
        "is_active",
    )


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "icon",
        "sort_order",
        "is_active",
    )

    list_display_links = (
        "title",
    )

    list_editable = (
        "sort_order",
        "is_active",
    )

    search_fields = (
        "title",
        "description",
    )

    ordering = (
        "sort_order",
        "id",
    )

    fields = (
        "title",
        "description",
        "icon",
        "sort_order",
        "is_active",
    )

    
class MenuItemInline(admin.TabularInline):

    model = MenuItem

    extra = 0

    ordering = [
        "order",
    ]

    fields = (
        "title",
        "url",
        "order",
        "is_active",
        "target",
    )


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "slug",
        "location",
        "is_active",
    )

    list_filter = (
        "location",
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
    )

    inlines = [
        MenuItemInline,
    ]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "menu",
        "url",
        "order",
        "is_active",
    )

    list_filter = (
        "menu",
        "is_active",
    )

    search_fields = (
        "title",
        "url",
    )

    ordering = (
        "menu",
        "order",
    )

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "slug",
        "status",
        "template",
        "updated_at",
    )

    list_filter = (
        "status",
        "template",
    )

    search_fields = (
        "title",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }



@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):

    list_display = (
        "question",
        "order",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "question",
        "answer",
    )

    ordering = (
        "order",
    )