
from django.shortcuts import render, get_object_or_404

from .models import Page,FAQ
from django.http import HttpResponse


def page_detail(request, slug):

    page = get_object_or_404(
        Page,
        slug=slug,
        status="published"
    )

    context = {
        "page": page,
    }

    return render(
        request,
        "cms/page_detail.html",
        context
    )


def faq_list(request):

    faqs = FAQ.objects.filter(
        is_active=True
    )

    context = {
        "faqs": faqs,
    }

    return render(
        request,
        "cms/faq.html",
        context
    )

def robots_txt(request):

    content = """
User-agent: *
Allow: /

Sitemap: /sitemap.xml
"""

    return HttpResponse(
        content,
        content_type="text/plain"
    )