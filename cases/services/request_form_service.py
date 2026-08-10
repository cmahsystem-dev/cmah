from django.core.exceptions import ValidationError
from django.db import transaction

from cases.models import RequestDocument
from cases.services.request_data_service import RequestDataService
from cases.services.request_document_service import RequestDocumentService
from services.models import ServiceField
from services.services.service_form_schema_service import (
    ServiceFormSchemaService,
)
from services.services.service_form_validation_service import (
    ServiceFormValidationService,
)


class RequestFormService:

    @staticmethod
    def ensure_editable(*, service_request) -> None:
        editable_statuses = {
            service_request.Status.DRAFT,
            service_request.Status.NEEDS_CORRECTION,
        }

        if service_request.status not in editable_statuses:
            raise ValidationError(
                "این درخواست در وضعیت فعلی قابل ویرایش نیست."
            )

    @staticmethod
    def get_form(*, service_request) -> dict:
        service = service_request.service

        schema = ServiceFormSchemaService.build(
            service=service,
        )

        field_keys = [
            field["key"]
            for field in schema
            if field["type"] != ServiceField.FieldType.FILE
        ]

        prefill = RequestDataService.build_prefill(
            user=service_request.user,
            field_keys=field_keys,
        )

        request_data = service_request.request_data or {}

        for key in field_keys:
            if key in request_data:
                prefill[key] = request_data[key]

        return {
            "schema": schema,
            "data": prefill,
        }

    @staticmethod
    def validate_required_files(
        *,
        service_request,
        files: dict | None = None,
    ) -> None:
        files = files or {}

        required_file_fields = ServiceField.objects.filter(
            service=service_request.service,
            is_active=True,
            field_type=ServiceField.FieldType.FILE,
            required=True,
        )

        errors = {}

        for field in required_file_fields:
            if files.get(field.key):
                continue

            has_existing_document = (
                service_request.documents
                .filter(
                    field_key=field.key,
                    status__in=[
                        RequestDocument.Status.PENDING,
                        RequestDocument.Status.APPROVED,
                    ],
                )
                .exists()
            )

            if not has_existing_document:
                errors[field.key] = (
                    "بارگذاری این مدرک الزامی است."
                )

        if errors:
            raise ValidationError(errors)


    @staticmethod
    @transaction.atomic
    def submit_form(
        *,
        service_request,
        data: dict,
        files: dict | None = None,
        uploaded_by=None,
    ) -> dict:
        files = files or {}

        # 1. اعتبارسنجی و ذخیره اطلاعات فرم
        cleaned_data = RequestFormService.save(
            service_request=service_request,
            data=data,
        )

        # 2. اعتبارسنجی مدارک اجباری
        RequestFormService.validate_required_files(
            service_request=service_request,
            files=files,
        )

        # 3. ذخیره فایل‌های جدید
        documents = RequestFormService.save_files(
            service_request=service_request,
            files=files,
            uploaded_by=uploaded_by,
        )

        return {
            "data": cleaned_data,
            "documents": documents,
    }   

    @staticmethod
    @transaction.atomic
    def save_files(
        *,
        service_request,
        files: dict,
        uploaded_by=None,
    ) -> list:
        RequestFormService.ensure_editable(
            service_request=service_request,
        )
        file_fields = {
            field.key: field
            for field in ServiceField.objects.filter(
                service=service_request.service,
                is_active=True,
                field_type=ServiceField.FieldType.FILE,
            )
        }

        documents = []

        for key, uploaded_file in files.items():
            field = file_fields.get(key)

            if field is None:
                continue

            document = RequestDocumentService.upload_new_version(
                service_request=service_request,
                field_key=key,
                file=uploaded_file,
                uploaded_by=uploaded_by,
            )

            documents.append(document)

        return documents

    @staticmethod
    @transaction.atomic
    def save(
        *,
        service_request,
        data: dict,
    ) -> dict:
        RequestFormService.ensure_editable(
            service_request=service_request,
        )
        
        cleaned_data = ServiceFormValidationService.validate(
            service=service_request.service,
            data=data,
        )

        reusable_fields = set(
            ServiceField.objects.filter(
                service=service_request.service,
                is_active=True,
                reusable=True,
            )
            .exclude(
                field_type=ServiceField.FieldType.FILE,
            )
            .values_list("key", flat=True)
        )

        RequestDataService.save_request_data(
            service_request=service_request,
            data=cleaned_data,
            reusable_fields=reusable_fields,
        )

        return cleaned_data