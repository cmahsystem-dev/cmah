from django.contrib.sitemaps import Sitemap

from .models import Page



class PageSitemap(Sitemap):

    changefreq = "weekly"

    priority = 0.8


    def items(self):

        return Page.objects.filter(
            status="published"
        )


    def location(self, obj):

        return f"/{obj.slug}/"