from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from cases.models import ServiceRequest
from cases.services.request_timeline_service import RequestTimelineService
from payments.models  import (
    GatewayProvider,
    Payment,
    PaymentMethod,
)


class PaymentService:

    @staticmethod
    @transaction.atomic
    def create_payment(
        *,
        service_request: ServiceRequest,
        method_code: str = "card_to_card",
        gateway_provider_code: str | None = None,
    ) -> Payment:
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=service_request.pk)
        )

        if (
            service_request.status
            != ServiceRequest.Status.READY_FOR_PAYMENT
        ):
            raise ValidationError(
                "درخواست در وضعیت فعلی آماده پرداخت نیست."
            )

        if service_request.amount <= 0:
            raise ValidationError(
                "این درخواست نیاز به پرداخت ندارد."
            )

        method_code = method_code.strip()

        if not method_code:
            raise ValidationError(
                "روش پرداخت الزامی است."
            )

        try:
            method = PaymentMethod.objects.get(
                code=method_code,
                is_active=True,
            )
        except PaymentMethod.DoesNotExist:
            raise ValidationError(
                "روش پرداخت معتبر یا فعال نیست."
            )

        gateway_provider = None

        if method.code == "gateway":
            gateway_provider_code = (
                gateway_provider_code or ""
            ).strip()

            if not gateway_provider_code:
                raise ValidationError(
                    "ارائه‌دهنده درگاه بانکی الزامی است."
                )

            try:
                gateway_provider = (
                    GatewayProvider.objects.get(
                        code=gateway_provider_code,
                        is_active=True,
                    )
                )
            except GatewayProvider.DoesNotExist:
                raise ValidationError(
                    "ارائه‌دهنده درگاه بانکی معتبر یا فعال نیست."
                )

        elif gateway_provider_code:
            raise ValidationError(
                "برای این روش پرداخت نباید درگاه بانکی تعیین شود."
            )

        paid_payment = (
            Payment.objects
            .filter(
                service_request=service_request,
                status=Payment.Status.PAID,
            )
            .first()
        )

        if paid_payment is not None:
            raise ValidationError(
                "این درخواست قبلاً پرداخت شده است."
            )

        awaiting_verification_payment = (
            Payment.objects
            .select_for_update()
            .filter(
                service_request=service_request,
                status=Payment.Status.AWAITING_VERIFICATION,
            )
            .first()
        )

        if awaiting_verification_payment is not None:
            raise ValidationError(
                "یک پرداخت در انتظار تأیید برای این درخواست وجود دارد."
            )

        pending_payment = (
            Payment.objects
            .select_for_update()
            .filter(
                service_request=service_request,
                status=Payment.Status.PENDING,
            )
            .order_by("-created_at")
            .first()
        )

        if pending_payment is not None:
            same_method = (
                pending_payment.method_id == method.pk
            )

            same_provider = (
                pending_payment.gateway_provider_id
                == (
                    gateway_provider.pk
                    if gateway_provider is not None
                    else None
                )
            )

            if same_method and same_provider:
                return pending_payment

            pending_payment.status = Payment.Status.CANCELLED
            pending_payment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            RequestTimelineService.record(
                service_request=service_request,
                event_type="payment",
                title="روش پرداخت تغییر کرد.",
                metadata={
                    "payment_id": pending_payment.pk,
                    "method": pending_payment.method.code,
                    "gateway_provider": (
                        pending_payment.gateway_provider.code
                        if pending_payment.gateway_provider
                        else None
                    ),
                },
            )

        payment = Payment.objects.create(
            service_request=service_request,
            amount=service_request.amount,
            method=method,
            gateway_provider=gateway_provider,
            status=Payment.Status.PENDING,
        )

        RequestTimelineService.record(
            service_request=service_request,
            event_type="payment",
            title="فرآیند پرداخت ایجاد شد.",
            metadata={
                "payment_id": payment.pk,
                "amount": payment.amount,
                "method": payment.method.code,
                "gateway_provider": (
                    payment.gateway_provider.code
                    if payment.gateway_provider
                    else None
                ),
            },
        )

        return payment

    @staticmethod
    def is_request_paid(
        *,
        service_request: ServiceRequest,
    ) -> bool:
        return Payment.objects.filter(
            service_request=service_request,
            status=Payment.Status.PAID,
        ).exists()

    @staticmethod
    @transaction.atomic
    def mark_paid(
        *,
        payment: Payment,
        reference_id: str,
        authority: str = "",
    ) -> Payment:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related("service_request")
            .get(pk=payment.pk)
        )

        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=payment.service_request_id)
        )

        reference_id = reference_id.strip()
        authority = authority.strip()

        if not reference_id:
            raise ValidationError(
                "شماره مرجع پرداخت الزامی است."
            )

        # Callback تکراری درگاه نباید پرداخت را دوباره انجام دهد.
        if payment.status == Payment.Status.PAID:
            return payment

        allowed_statuses = {
            Payment.Status.PENDING,
            Payment.Status.AWAITING_VERIFICATION,
        }

        if payment.status not in allowed_statuses:
            raise ValidationError(
                "این پرداخت دیگر قابل تأیید نیست."
            )

        if service_request.status != ServiceRequest.Status.READY_FOR_PAYMENT:
            raise ValidationError(
                "وضعیت درخواست برای تأیید پرداخت معتبر نیست."
            )

        if payment.amount != service_request.amount:
            raise ValidationError(
                "مبلغ پرداخت با مبلغ درخواست مطابقت ندارد."
            )

        already_paid = (
            Payment.objects
            .exclude(pk=payment.pk)
            .filter(
                service_request=service_request,
                status=Payment.Status.PAID,
            )
            .exists()
        )

        if already_paid:
            raise ValidationError(
                "این درخواست قبلاً پرداخت شده است."
            )

        payment.status = Payment.Status.PAID
        payment.reference_id = reference_id
        payment.authority = authority
        payment.paid_at = timezone.now()

        payment.save(
            update_fields=[
                "status",
                "reference_id",
                "authority",
                "paid_at",
                "updated_at",
            ]
        )

        RequestTimelineService.record(
            service_request=service_request,
            event_type="payment",
            title="پرداخت با موفقیت انجام شد.",
            metadata={
                "payment_id": payment.pk,
                "amount": payment.amount,
                "method": payment.method.code,
                "gateway_provider": (
                    payment.gateway_provider.code
                    if payment.gateway_provider
                    else None
                ),
                "reference_id": payment.reference_id,
            },
        )

        service_request.transition_to(
            ServiceRequest.Status.PAID,
            note="پرداخت با موفقیت تأیید شد.",
        )

        return payment


    @staticmethod
    @transaction.atomic
    def mark_failed(
        *,
        payment: Payment,
    ) -> Payment:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related("service_request")
            .get(pk=payment.pk)
        )

        if payment.status == Payment.Status.FAILED:
            return payment

        allowed_statuses = {
            Payment.Status.PENDING,
            Payment.Status.AWAITING_VERIFICATION,
        }

        if payment.status not in allowed_statuses:
            raise ValidationError(
                "این پرداخت قابل ثبت به‌عنوان ناموفق نیست."
            )

        payment.status = Payment.Status.FAILED

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        RequestTimelineService.record(
            service_request=payment.service_request,
            event_type="payment",
            title="پرداخت ناموفق بود.",
            metadata={
                "payment_id": payment.pk,
                "amount": payment.amount,
                "method": payment.method.code,
                "gateway_provider": (
                    payment.gateway_provider.code
                    if payment.gateway_provider
                    else None
                ),
            },
        )

        return payment


    @staticmethod
    @transaction.atomic
    def cancel(
        *,
        payment: Payment,
    ) -> Payment:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related("service_request")
            .get(pk=payment.pk)
        )

        if payment.status == Payment.Status.CANCELLED:
            return payment

        if payment.status != Payment.Status.PENDING:
            raise ValidationError(
                "این پرداخت قابل لغو نیست."
            )

        payment.status = Payment.Status.CANCELLED

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        RequestTimelineService.record(
            service_request=payment.service_request,
            event_type="payment",
            title="پرداخت لغو شد.",
            metadata={
                "payment_id": payment.pk,
                "amount": payment.amount,
                "method": payment.method.code,
                "gateway_provider": (
                    payment.gateway_provider.code
                    if payment.gateway_provider
                    else None
                ),
            },
        )

        return payment