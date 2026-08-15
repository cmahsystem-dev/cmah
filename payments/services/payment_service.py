from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from cases.models import ServiceRequest
from cases.services.request_timeline_service import RequestTimelineService
from payments.models import Payment


class PaymentService:

    @staticmethod
    @transaction.atomic
    def create_payment(
        *,
        service_request: ServiceRequest,
        gateway: str = Payment.Gateway.MANUAL,
    ) -> Payment:
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=service_request.pk)
        )

        if service_request.status != ServiceRequest.Status.READY_FOR_PAYMENT:
            raise ValidationError(
                "درخواست در وضعیت فعلی آماده پرداخت نیست."
            )

        if service_request.amount <= 0:
            raise ValidationError(
                "این درخواست نیاز به پرداخت ندارد."
            )

        if gateway not in Payment.Gateway.values:
            raise ValidationError(
                "درگاه پرداخت نامعتبر است."
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
            return pending_payment

        payment = Payment.objects.create(
            service_request=service_request,
            amount=service_request.amount,
            gateway=gateway,
            status=Payment.Status.PENDING,
        )

        RequestTimelineService.record(
            service_request=service_request,
            event_type="payment",
            title="فرآیند پرداخت ایجاد شد.",
            metadata={
                "payment_id": payment.pk,
                "amount": payment.amount,
                "gateway": payment.gateway,
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

        if payment.status != Payment.Status.PENDING:
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
                "gateway": payment.gateway,
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

        if payment.status != Payment.Status.PENDING:
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
                "gateway": payment.gateway,
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
                "gateway": payment.gateway,
            },
        )

        return payment