from django.db import transaction

from cases.models import RequestDocument, ServiceRequest
from cases.services.request_timeline_service import RequestTimelineService

class RequestDocumentService:

    @staticmethod
    @transaction.atomic
    def upload_new_version(
        *,
        service_request: ServiceRequest,
        field_key: str,
        file,
        uploaded_by=None,
    ) -> RequestDocument:
        latest_document = (
            RequestDocument.objects
            .select_for_update()
            .filter(
                service_request=service_request,
                field_key=field_key,
            )
            .order_by("-version")
            .first()
        )

        if latest_document is None:
            next_version = 1

        else:
            next_version = latest_document.version + 1

            if latest_document.status != RequestDocument.Status.REPLACED:
                latest_document.status = RequestDocument.Status.REPLACED
                latest_document.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

        document = RequestDocument.objects.create(
            service_request=service_request,
            field_key=field_key,
            file=file,
            version=next_version,
            status=RequestDocument.Status.PENDING,
            uploaded_by=uploaded_by,
        )

        RequestTimelineService.record(
            service_request=service_request,
            event_type="document_uploaded",
            title="مدرک جدید بارگذاری شد.",
            actor=uploaded_by,
            metadata={
                "document_id": document.pk,
                "field_key": document.field_key,
                "version": document.version,
            },
        )

        return document

    @staticmethod
    @transaction.atomic
    def approve(
        document: RequestDocument,
    ) -> RequestDocument:
        document = (
            RequestDocument.objects
            .select_for_update()
            .get(pk=document.pk)
        )

        if document.status != RequestDocument.Status.PENDING:
            raise ValueError(
                "فقط مدرک در انتظار بررسی قابل تأیید است."
            )

        document.status = RequestDocument.Status.APPROVED
        document.rejection_reason = ""

        document.save(
            update_fields=[
                "status",
                "rejection_reason",
                "updated_at",
            ]
        )
        RequestTimelineService.record(
            service_request=document.service_request,
            event_type="document_approved",
            title="مدرک تأیید شد.",
            actor=None,
            metadata={
                "document_id": document.pk,
                "field_key": document.field_key,
                "version": document.version,
            },
        )
        return document

    @staticmethod
    @transaction.atomic
    def reject(
        document: RequestDocument,
        reason: str,
    ) -> RequestDocument:
        reason = reason.strip()

        if not reason:
            raise ValueError(
                "دلیل رد مدرک الزامی است."
            )

        document = (
            RequestDocument.objects
            .select_for_update()
            .get(pk=document.pk)
        )

        if document.status != RequestDocument.Status.PENDING:
            raise ValueError(
                "فقط مدرک در انتظار بررسی قابل رد است."
            )

        document.status = RequestDocument.Status.REJECTED
        document.rejection_reason = reason

        document.save(
            update_fields=[
                "status",
                "rejection_reason",
                "updated_at",
            ]
        )
        RequestTimelineService.record(
            service_request=document.service_request,
            event_type="document_rejected",
            title="مدرک رد شد.",
            description=reason,
            actor=None,
            metadata={
                "document_id": document.pk,
                "field_key": document.field_key,
                "version": document.version,
            },
        )
        return document