from .models import SiteSetting,Menu


def site_settings(request):
    return {
        "site": SiteSetting.objects.first(),

        "header_menu":Menu.objects.filter(
            slug="header",
            is_active=True
        ).first(),
        
        "footer_menu":Menu.objects.filter(
            slug="footer",
            is_active=True,
        ).first
    }