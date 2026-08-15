from django.core.exceptions import ValidationError
from django.db import transaction

from cases.models import ServiceRequest
from payments.services.payment_service import PaymentService


class RequestRoutingService:

    @staticmethod
    @transaction.atomic
    def route_submitted(
        *,
        service_request: ServiceRequest,
        changed_by=None,
    ) -> ServiceRequest:
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=service_request.pk)
        )

        if service_request.status != ServiceRequest.Status.SUBMITTED:
            raise ValidationError(
                "فقط درخواست ثبت‌شده قابل مسیریابی است."
            )

        # خدمات رایگان مستقیماً وارد صف بررسی می‌شوند.
        if service_request.amount == 0:
            service_request.transition_to(
                ServiceRequest.Status.UNDER_REVIEW,
                changed_by=changed_by,
                note="درخواست رایگان برای بررسی ارسال شد.",
            )

            return service_request

        # اگر درخواست قبلاً پرداخت شده باشد،
        # بعد از اصلاح دوباره نیاز به پرداخت ندارد.
        if PaymentService.is_request_paid(
            service_request=service_request,
        ):
            service_request.transition_to(
                ServiceRequest.Status.UNDER_REVIEW,
                changed_by=changed_by,
                note="درخواست قبلاً پرداخت شده و برای بررسی مجدد ارسال شد.",
            )

            return service_request

        # درخواست پولی که هنوز پرداخت نشده است.
        service_request.transition_to(
            ServiceRequest.Status.READY_FOR_PAYMENT,
            changed_by=changed_by,
            note="درخواست آماده پرداخت است.",
        )

        return service_request