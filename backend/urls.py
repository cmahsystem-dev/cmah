"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views.
For more information see:
https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from cms.sitemaps import PageSitemap


sitemaps = {
    "pages": PageSitemap,
}


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "ckeditor5/",
        include("django_ckeditor_5.urls"),
    ),

    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="sitemap",
    ),

    path(
        "accounts/",
        include("accounts.urls"),
    ),

    path(
        "services/",
        include("services.urls"),
    ),

    path(
        "",
        include("core.urls"),
    ),

    path(
        "",
        include("cms.urls"),
    ),

        path(
        "requests/",
        include("cases.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )