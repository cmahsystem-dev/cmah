from django.shortcuts import render

from cms.models import (
    Feature,
    HeroSection,
    HomePageSetting,
    ProcessStep,
    Statistic,
    TrustItem,
)
from services.models import Service


def home(request):
    hero = (
        HeroSection.objects
        .filter(is_active=True)
        .order_by("sort_order", "id")
        .first()
    )

    home_settings = HomePageSetting.objects.first()

    trust_items = TrustItem.objects.filter(
        is_active=True,
    ).order_by(
        "sort_order",
        "id",
    )

    process_steps = ProcessStep.objects.filter(
        is_active=True,
    ).order_by(
        "sort_order",
        "id",
    )

    statistics = Statistic.objects.filter(
        is_active=True,
    ).order_by(
        "sort_order",
        "id",
    )

    features = Feature.objects.filter(
        is_active=True,
    ).order_by(
        "sort_order",
        "id",
    )

    featured_services = (
        Service.objects
        .filter(
            is_active=True,
            is_featured=True,
        )
        .select_related("category")
        .order_by(
            "sort_order",
            "title",
        )[:8]
    )

    context = {
        "hero": hero,
        "home_settings": home_settings,
        "trust_items": trust_items,
        "process_steps": process_steps,
        "statistics": statistics,
        "features": features,
        "featured_services": featured_services,
    }

    return render(request, "home.html", context)