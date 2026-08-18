from django.db import migrations


def migrate_legacy_payment_methods(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    PaymentMethod = apps.get_model("payments", "PaymentMethod")
    GatewayProvider = apps.get_model("payments", "GatewayProvider")

    card_to_card_method, _ = PaymentMethod.objects.get_or_create(
        code="card_to_card",
        defaults={
            "title": "کارت به کارت",
            "description": "پرداخت از طریق انتقال کارت به کارت",
            "is_active": True,
            "priority": 10,
        },
    )

    PaymentMethod.objects.get_or_create(
        code="wallet",
        defaults={
            "title": "کیف پول",
            "description": "پرداخت از طریق کیف پول CMAH",
            "is_active": False,
            "priority": 20,
        },
    )

    gateway_method, _ = PaymentMethod.objects.get_or_create(
        code="gateway",
        defaults={
            "title": "درگاه بانکی",
            "description": "پرداخت آنلاین از طریق درگاه بانکی",
            "is_active": False,
            "priority": 30,
        },
    )

    zarinpal_provider, _ = GatewayProvider.objects.get_or_create(
        code="zarinpal",
        defaults={
            "title": "زرین‌پال",
            "description": "Provider قدیمی برای حفظ سوابق پرداخت",
            "is_active": False,
            "priority": 100,
        },
    )

    idpay_provider, _ = GatewayProvider.objects.get_or_create(
        code="idpay",
        defaults={
            "title": "آیدی‌پی",
            "description": "Provider قدیمی برای حفظ سوابق پرداخت",
            "is_active": False,
            "priority": 110,
        },
    )

    Payment.objects.filter(
        gateway="manual",
        method__isnull=True,
    ).update(
        method=card_to_card_method,
        gateway_provider=None,
    )

    Payment.objects.filter(
        gateway="zarinpal",
        method__isnull=True,
    ).update(
        method=gateway_method,
        gateway_provider=zarinpal_provider,
    )

    Payment.objects.filter(
        gateway="idpay",
        method__isnull=True,
    ).update(
        method=gateway_method,
        gateway_provider=idpay_provider,
    )


def reverse_legacy_payment_methods(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")

    Payment.objects.update(
        method=None,
        gateway_provider=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "payments",
            "0002_gatewayprovider_paymentmethod_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            migrate_legacy_payment_methods,
            reverse_legacy_payment_methods,
        ),
    ]