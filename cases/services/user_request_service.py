from django.core.exceptions import ValidationError
from django.db import transaction

from cases.models import ServiceRequest
from cases.services.request_form_service import RequestFormService

from cases.services.request_routing_service import RequestRoutingService


class UserRequestService:

    @staticmethod
    def ensure_owner(
        *,
        service_request: ServiceRequest,
        user,
    ) -> None:
        if service_request.user_id != user.id:
            raise ValidationError(
                "شما اجازه انجام این عملیات روی این درخواست را ندارید."
            )

    @staticmethod
    def ensure_status(
        *,
        service_request: ServiceRequest,
        allowed_statuses: set,
    ) -> None:
        if service_request.status not in allowed_statuses:
            raise ValidationError(
                "این عملیات در وضعیت فعلی درخواست مجاز نیست."
            )

    @staticmethod
    @transaction.atomic
    def create_draft(
        *,
        user,
        service,
    ) -> ServiceRequest:
        if not user or not user.is_authenticated:
            raise ValidationError(
                "برای ایجاد درخواست باید وارد حساب کاربری شوید."
            )

        if not service.is_active:
            raise ValidationError(
                "این خدمت در حال حاضر فعال نیست."
            )

        service_request = ServiceRequest.objects.create(
            user=user,
            service=service,
            amount=service.total_price,
            status=ServiceRequest.Status.DRAFT,
        )

        return service_request


    @staticmethod
    @transaction.atomic
    def save_form(
        *,
        service_request: ServiceRequest,
        user,
        data: dict,
        files: dict | None = None,
    ) -> dict:
        UserRequestService.ensure_owner(
            service_request=service_request,
            user=user,
        )

        UserRequestService.ensure_status(
            service_request=service_request,
            allowed_statuses={
                ServiceRequest.Status.DRAFT,
                ServiceRequest.Status.NEEDS_CORRECTION,
            },
        )

        return RequestFormService.submit_form(
            service_request=service_request,
            data=data,
            files=files,
            uploaded_by=user,
        )

    @staticmethod
    @transaction.atomic
    def submit(
        *,
        service_request: ServiceRequest,
        user,
    ) -> ServiceRequest:
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=service_request.pk)
        )

        UserRequestService.ensure_owner(
            service_request=service_request,
            user=user,
        )

        UserRequestService.ensure_status(
            service_request=service_request,
            allowed_statuses={
                ServiceRequest.Status.DRAFT,
                ServiceRequest.Status.NEEDS_CORRECTION,
            },
        )

        service_request.transition_to(
            ServiceRequest.Status.SUBMITTED,
            changed_by=user,
            note="درخواست توسط کاربر ثبت شد.",
        )

        return RequestRoutingService.route_submitted(
            service_request=service_request,
            changed_by=user,
        )