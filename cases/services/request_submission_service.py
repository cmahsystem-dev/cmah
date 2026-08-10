from django.core.exceptions import ValidationError
from django.db import transaction

from cases.models import ServiceRequest
from cases.services.request_form_service import RequestFormService
from services.models import ServiceField


class RequestSubmissionService:

    @staticmethod
    @transaction.atomic
    def submit(
        *,
        service_request,
        changed_by=None,
        note: str = "",
    ) -> None:
        # فقط Draft یا درخواست نیازمند اصلاح قابلیت ثبت مجدد دارد.
        if service_request.status not in {
            ServiceRequest.Status.DRAFT,
            ServiceRequest.Status.NEEDS_CORRECTION,
        }:
            raise ValidationError(
                "این درخواست در وضعیت فعلی قابل ثبت نیست."
            )

        # بررسی فیلدهای غیر فایلی الزامی
        required_fields = (
            ServiceField.objects
            .filter(
                service=service_request.service,
                is_active=True,
                required=True,
            )
            .exclude(
                field_type=ServiceField.FieldType.FILE,
            )
        )

        request_data = service_request.request_data or {}
        errors = {}

        for field in required_fields:
            value = request_data.get(field.key)

            is_empty = (
                value is None
                or value == ""
                or value == []
            )

            if is_empty:
                errors[field.key] = "این فیلد الزامی است."

        if errors:
            raise ValidationError(errors)

        # بررسی مدارک الزامی
        RequestFormService.validate_required_files(
            service_request=service_request,
            files={},
        )

        # تمام Guardها پاس شده‌اند؛ حالا Domain transition اجرا شود.
        service_request.transition_to(
            ServiceRequest.Status.SUBMITTED,
            changed_by=changed_by,
            note=note,
        )