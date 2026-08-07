from django.shortcuts import render, get_object_or_404

from .models import Service


def service_list(request):

    services = (
        Service.objects
        .filter(is_active=True)
        .select_related("category")
        .order_by(
            "category__sort_order",
            "sort_order",
            "title"
        )
    )

    return render(
        request,
        "services/service_list.html",
        {
            "services": services
        }
    )


def service_detail(request, slug):

    service = get_object_or_404(
        Service.objects.select_related("category"),
        slug=slug,
        is_active=True
    )

    related_services = (
        Service.objects
        .filter(
            category=service.category,
            is_active=True
        )
        .exclude(id=service.id)[:4]
    )

    faqs = service.faqs.filter(
        is_active=True
    )

    context = {
        "service": service,
        "faqs": faqs,
        "related_services": related_services,
    }

    return render(
        request,
        "services/service_detail.html",
        context
    )