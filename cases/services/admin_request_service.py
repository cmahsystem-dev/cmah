from django.core.exceptions import ValidationError
from django.db import transaction

from cases.models import ServiceRequest
from cases.services.request_document_service import RequestDocumentService
from services.models import ServiceField


class AdminRequestService:

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
    def start_review(
        *,
        service_request: ServiceRequest,
        changed_by=None,
    ) -> ServiceRequest:
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=service_request.pk)
        )

        AdminRequestService.ensure_status(
            service_request=service_request,
            allowed_statuses={
                ServiceRequest.Status.PAID,
                ServiceRequest.Status.SUBMITTED,
            },
        )

        if (
            service_request.status == ServiceRequest.Status.SUBMITTED
            and service_request.amount > 0
        ):
            raise ValidationError(
                "درخواست پولی قبل از بررسی باید پرداخت شده باشد."
            )

        service_request.transition_to(
            ServiceRequest.Status.UNDER_REVIEW,
            changed_by=changed_by,
            note="بررسی درخواست توسط اپراتور آغاز شد.",
        )

        return service_request

    @staticmethod
    @transaction.atomic
    def request_correction(
        *,
        service_request: ServiceRequest,
        changed_by=None,
        note: str,
    ) -> ServiceRequest:
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=service_request.pk)
        )

        AdminRequestService.ensure_status(
            service_request=service_request,
            allowed_statuses={
                ServiceRequest.Status.UNDER_REVIEW,
            },
        )

        note = note.strip()

        if not note:
            raise ValidationError(
                "دلیل نیاز به اصلاح الزامی است."
            )

        service_request.transition_to(
            ServiceRequest.Status.NEEDS_CORRECTION,
            changed_by=changed_by,
            note=note,
        )

        return service_request

    @staticmethod
    @transaction.atomic
    def start_processing(
        *,
        service_request: ServiceRequest,
        changed_by=None,
        note: str = "",
    ) -> ServiceRequest:
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=service_request.pk)
        )

        AdminRequestService.ensure_status(
            service_request=service_request,
            allowed_statuses={
                ServiceRequest.Status.UNDER_REVIEW,
            },
        )

        AdminRequestService.ensure_required_documents_approved(
            service_request=service_request,
        )

        service_request.transition_to(
            ServiceRequest.Status.PROCESSING,
            changed_by=changed_by,
            note=note.strip() or "بررسی درخواست تأیید شد و انجام خدمت آغاز شد.",
        )

        return service_request


    @staticmethod
    @transaction.atomic
    def complete(
        *,
        service_request: ServiceRequest,
        changed_by=None,
        note: str = "",
    ) -> ServiceRequest:
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=service_request.pk)
        )

        AdminRequestService.ensure_status(
            service_request=service_request,
            allowed_statuses={
                ServiceRequest.Status.PROCESSING,
            },
        )

        service_request.transition_to(
            ServiceRequest.Status.COMPLETED,
            changed_by=changed_by,
            note=note.strip() or "انجام خدمت با موفقیت تکمیل شد.",
        )

        return service_request


    @staticmethod
    @transaction.atomic
    def reject_request(
        *,
        service_request: ServiceRequest,
        changed_by=None,
        note: str,
    ) -> ServiceRequest:
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=service_request.pk)
        )

        AdminRequestService.ensure_status(
            service_request=service_request,
            allowed_statuses={
                ServiceRequest.Status.UNDER_REVIEW,
            },
        )

        note = note.strip()

        if not note:
            raise ValidationError(
                "دلیل رد درخواست الزامی است."
            )

        service_request.transition_to(
            ServiceRequest.Status.REJECTED,
            changed_by=changed_by,
            note=note,
        )

        return service_request


    @staticmethod
    @transaction.atomic
    def approve_document(
        *,
        document,
        changed_by=None,
    ):
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=document.service_request_id)
        )

        AdminRequestService.ensure_status(
            service_request=service_request,
            allowed_statuses={
                ServiceRequest.Status.UNDER_REVIEW,
            },
        )

        return RequestDocumentService.approve(
            document=document,
            reviewed_by=changed_by,
        )


   

    @staticmethod
    @transaction.atomic
    def reject_document(
        *,
        document,
        changed_by=None,
        reason: str,
    ):
        service_request = (
            ServiceRequest.objects
            .select_for_update()
            .get(pk=document.service_request_id)
        )

        AdminRequestService.ensure_status(
            service_request=service_request,
            allowed_statuses={
                ServiceRequest.Status.UNDER_REVIEW,
            },
        )

        reason = reason.strip()

        if not reason:
            raise ValidationError(
                "دلیل رد مدرک الزامی است."
            )

        return RequestDocumentService.reject(
            document=document,
            reason=reason,
            reviewed_by=changed_by,
        )

    @staticmethod
    def ensure_required_documents_approved(
        *,
        service_request: ServiceRequest,
    ) -> None:
        required_file_fields = ServiceField.objects.filter(
            service=service_request.service,
            is_active=True,
            required=True,
            field_type=ServiceField.FieldType.FILE,
        )

        errors = {}

        for field in required_file_fields:
            has_approved_document = service_request.documents.filter(
                field_key=field.key,
                status="approved",
            ).exists()

            if not has_approved_document:
                errors[field.key] = (
                    "این مدرک هنوز تأیید نشده است."
                )

        if errors:
            raise ValidationError(errors)