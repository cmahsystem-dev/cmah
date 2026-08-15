from django.test import TestCase

# Create your tests here.
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import TestCase

from accounts.models import User
from cases.models import (
    RequestDocument,
    ServiceRequest,
)
from cases.services.request_document_service import (
    RequestDocumentService,
)
from cases.services.request_form_service import RequestFormService
from cases.services.request_submission_service import (
    RequestSubmissionService,
)
from services.models import Service, ServiceField
from cases.services.request_routing_service import RequestRoutingService
from payments.services.payment_service import PaymentService


class ServiceRequestFlowTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            mobile="09120000000",
        )

        # اگر Service شما فیلد اجباری دیگری دارد،
        # فقط همین بخش create را مطابق مدل Service تنظیم کن.
        self.service = Service.objects.create(
            title="خدمت تست",
            slug="test-service",
        )

        self._create_service_fields()

        self.request = ServiceRequest.objects.create(
            user=self.user,
            service=self.service,
            amount=100_000,
        )

    def _create_service_fields(self):
        ServiceField.objects.create(
            service=self.service,
            key="national_code",
            label="کد ملی",
            field_type=ServiceField.FieldType.TEXT,
            required=True,
            reusable=True,
            order=1,
        )

        ServiceField.objects.create(
            service=self.service,
            key="age",
            label="سن",
            field_type=ServiceField.FieldType.NUMBER,
            required=True,
            reusable=True,
            order=2,
        )

        ServiceField.objects.create(
            service=self.service,
            key="gender",
            label="جنسیت",
            field_type=ServiceField.FieldType.SELECT,
            required=True,
            reusable=True,
            order=3,
            choices=[
                {
                    "value": "male",
                    "label": "مرد",
                },
                {
                    "value": "female",
                    "label": "زن",
                },
            ],
        )

        ServiceField.objects.create(
            service=self.service,
            key="terms_accepted",
            label="پذیرش قوانین",
            field_type=ServiceField.FieldType.CHECKBOX,
            required=True,
            reusable=False,
            order=4,
        )

        ServiceField.objects.create(
            service=self.service,
            key="birth_date",
            label="تاریخ تولد",
            field_type=ServiceField.FieldType.DATE,
            required=True,
            reusable=True,
            order=5,
        )

        ServiceField.objects.create(
            service=self.service,
            key="national_card",
            label="تصویر کارت ملی",
            field_type=ServiceField.FieldType.FILE,
            required=True,
            reusable=False,
            order=6,
        )

    def _valid_data(self):
        return {
            "national_code": "0012345678",
            "age": "30",
            "gender": "male",
            "terms_accepted": True,
            "birth_date": "2000-05-21",
        }

    def _national_card_file(self, name="national-card.jpg"):
        return ContentFile(
            b"fake national card",
            name=name,
        )

    def _complete_request(self):
        return RequestFormService.submit_form(
            service_request=self.request,
            data=self._valid_data(),
            files={
                "national_card": self._national_card_file(),
            },
            uploaded_by=self.user,
        )

    # --------------------------------------------------
    # FORM VALIDATION
    # --------------------------------------------------

    def test_required_field_blocks_invalid_form(self):
        data = self._valid_data()
        data.pop("national_code")

        with self.assertRaises(ValidationError):
            RequestFormService.save(
                service_request=self.request,
                data=data,
            )

    def test_invalid_number_is_rejected(self):
        data = self._valid_data()
        data["age"] = "invalid"

        with self.assertRaises(ValidationError):
            RequestFormService.save(
                service_request=self.request,
                data=data,
            )

    def test_invalid_select_value_is_rejected(self):
        data = self._valid_data()
        data["gender"] = "invalid"

        with self.assertRaises(ValidationError):
            RequestFormService.save(
                service_request=self.request,
                data=data,
            )

    def test_invalid_date_is_rejected(self):
        data = self._valid_data()
        data["birth_date"] = "2000-02-30"

        with self.assertRaises(ValidationError):
            RequestFormService.save(
                service_request=self.request,
                data=data,
            )

    # --------------------------------------------------
    # USER ATTRIBUTE / SNAPSHOT
    # --------------------------------------------------

    def test_reusable_data_is_saved_for_user(self):
        RequestFormService.save(
            service_request=self.request,
            data=self._valid_data(),
        )

        attribute = self.user.attributes.get(
            key="national_code",
        )

        self.assertEqual(
            attribute.value,
            "0012345678",
        )

    def test_request_data_snapshot_is_saved(self):
        RequestFormService.save(
            service_request=self.request,
            data=self._valid_data(),
        )

        self.request.refresh_from_db()

        self.assertEqual(
            self.request.request_data["national_code"],
            "0012345678",
        )

        self.assertEqual(
            self.request.request_data["age"],
            30,
        )

    # --------------------------------------------------
    # REQUIRED DOCUMENT
    # --------------------------------------------------

    def test_missing_required_document_blocks_submission(self):
        RequestFormService.save(
            service_request=self.request,
            data=self._valid_data(),
        )

        with self.assertRaises(ValidationError):
            RequestSubmissionService.submit(
                service_request=self.request,
                changed_by=self.user,
            )

        self.request.refresh_from_db()

        self.assertEqual(
            self.request.status,
            ServiceRequest.Status.DRAFT,
        )

        self.assertIsNone(
            self.request.submitted_at,
        )

    # --------------------------------------------------
    # DOCUMENT VERSIONING
    # --------------------------------------------------

    def test_document_versioning_replaces_previous_version(self):
        document_v1 = RequestDocumentService.upload_new_version(
            service_request=self.request,
            field_key="national_card",
            file=self._national_card_file(
                "national-card-v1.jpg"
            ),
            uploaded_by=self.user,
        )

        document_v2 = RequestDocumentService.upload_new_version(
            service_request=self.request,
            field_key="national_card",
            file=self._national_card_file(
                "national-card-v2.jpg"
            ),
            uploaded_by=self.user,
        )

        document_v1.refresh_from_db()
        document_v2.refresh_from_db()

        self.assertEqual(
            document_v1.version,
            1,
        )

        self.assertEqual(
            document_v1.status,
            RequestDocument.Status.REPLACED,
        )

        self.assertEqual(
            document_v2.version,
            2,
        )

        self.assertEqual(
            document_v2.status,
            RequestDocument.Status.PENDING,
        )

    # --------------------------------------------------
    # FINAL SUBMIT
    # --------------------------------------------------

    def test_complete_request_can_be_submitted(self):
        self._complete_request()

        RequestSubmissionService.submit(
            service_request=self.request,
            changed_by=self.user,
            note="ثبت نهایی تست",
        )

        self.request.refresh_from_db()

        self.assertEqual(
            self.request.status,
            ServiceRequest.Status.SUBMITTED,
        )

        self.assertIsNotNone(
            self.request.submitted_at,
        )

    # --------------------------------------------------
    # HISTORY / TIMELINE
    # --------------------------------------------------

    def test_submission_creates_status_history(self):
        self._complete_request()

        RequestSubmissionService.submit(
            service_request=self.request,
            changed_by=self.user,
            note="ثبت نهایی تست",
        )

        history = self.request.status_history.get()

        self.assertEqual(
            history.from_status,
            ServiceRequest.Status.DRAFT,
        )

        self.assertEqual(
            history.to_status,
            ServiceRequest.Status.SUBMITTED,
        )

        self.assertEqual(
            history.note,
            "ثبت نهایی تست",
        )

    def test_submission_creates_timeline_event(self):
        self._complete_request()

        RequestSubmissionService.submit(
            service_request=self.request,
            changed_by=self.user,
        )

        self.assertTrue(
            self.request.timeline.filter(
                event_type="status_changed",
            ).exists()
        )

    # --------------------------------------------------
    # EDIT GUARD
    # --------------------------------------------------

    def test_submitted_request_cannot_be_edited(self):
        self._complete_request()

        RequestSubmissionService.submit(
            service_request=self.request,
            changed_by=self.user,
        )

        with self.assertRaises(ValidationError):
            RequestFormService.save(
                service_request=self.request,
                data=self._valid_data(),
            )

    def test_submitted_request_cannot_upload_document(self):
        self._complete_request()

        RequestSubmissionService.submit(
            service_request=self.request,
            changed_by=self.user,
        )

        with self.assertRaises(ValidationError):
            RequestFormService.save_files(
                service_request=self.request,
                files={
                    "national_card": self._national_card_file(
                        "blocked.jpg"
                    ),
                },
                uploaded_by=self.user,
            )

    # --------------------------------------------------
    # CORRECTION FLOW
    # --------------------------------------------------

    def test_needs_correction_allows_editing(self):
        self._complete_request()

        RequestSubmissionService.submit(
            service_request=self.request,
            changed_by=self.user,
        )

        self.request.transition_to(
            ServiceRequest.Status.UNDER_REVIEW,
            changed_by=self.user,
        )

        self.request.transition_to(
            ServiceRequest.Status.NEEDS_CORRECTION,
            changed_by=self.user,
        )

        updated_data = self._valid_data()
        updated_data["age"] = "31"

        result = RequestFormService.save(
            service_request=self.request,
            data=updated_data,
        )

        self.assertEqual(
            result["age"],
            31,
        )

    # --------------------------------------------------
    # REJECTED DOCUMENT
    # --------------------------------------------------

    def test_rejected_required_document_blocks_resubmission(self):
        self._complete_request()

        RequestSubmissionService.submit(
            service_request=self.request,
            changed_by=self.user,
        )

        self.request.transition_to(
            ServiceRequest.Status.UNDER_REVIEW,
            changed_by=self.user,
        )

        document = (
            self.request.documents
            .filter(
                field_key="national_card",
                status=RequestDocument.Status.PENDING,
            )
            .latest("version")
        )

        RequestDocumentService.reject(
            document,
            reason="تصویر خوانا نیست.",
        )

        self.request.transition_to(
            ServiceRequest.Status.NEEDS_CORRECTION,
            changed_by=self.user,
        )

        with self.assertRaises(ValidationError):
            RequestSubmissionService.submit(
                service_request=self.request,
                changed_by=self.user,
            )

        self.request.refresh_from_db()

        self.assertEqual(
            self.request.status,
            ServiceRequest.Status.NEEDS_CORRECTION,
        )

    def test_corrected_document_allows_resubmission(self):
        self._complete_request()

        RequestSubmissionService.submit(
            service_request=self.request,
            changed_by=self.user,
        )

        self.request.transition_to(
            ServiceRequest.Status.UNDER_REVIEW,
            changed_by=self.user,
        )

        document = (
            self.request.documents
            .filter(
                field_key="national_card",
                status=RequestDocument.Status.PENDING,
            )
            .latest("version")
        )

        RequestDocumentService.reject(
            document,
            reason="تصویر خوانا نیست.",
        )

        self.request.transition_to(
            ServiceRequest.Status.NEEDS_CORRECTION,
            changed_by=self.user,
        )

        RequestFormService.save_files(
            service_request=self.request,
            files={
                "national_card": self._national_card_file(
                    "national-card-corrected.jpg"
                ),
            },
            uploaded_by=self.user,
        )

        RequestSubmissionService.submit(
            service_request=self.request,
            changed_by=self.user,
        )

        self.request.refresh_from_db()

        self.assertEqual(
            self.request.status,
            ServiceRequest.Status.SUBMITTED,
        )


    def test_unpaid_request_routes_to_payment(self):
        service_request = ServiceRequest.objects.create(
            user=self.user,
            service=self.service,
            amount=250_000,
        )

        service_request.transition_to(
            ServiceRequest.Status.SUBMITTED,
            changed_by=self.user,
        )

        service_request = RequestRoutingService.route_submitted(
            service_request=service_request,
            changed_by=self.user,
        )

        self.assertEqual(
            service_request.status,
            ServiceRequest.Status.READY_FOR_PAYMENT,
        )


    def test_free_request_routes_directly_to_review(self):
        service_request = ServiceRequest.objects.create(
            user=self.user,
            service=self.service,
            amount=0,
        )

        service_request.transition_to(
            ServiceRequest.Status.SUBMITTED,
            changed_by=self.user,
        )

        service_request = RequestRoutingService.route_submitted(
            service_request=service_request,
            changed_by=self.user,
        )

        self.assertEqual(
            service_request.status,
            ServiceRequest.Status.UNDER_REVIEW,
        )

        self.assertFalse(
            service_request.payments.exists()
        )


    def test_paid_corrected_request_routes_to_review_without_new_payment(self):
        service_request = ServiceRequest.objects.create(
            user=self.user,
            service=self.service,
            amount=250_000,
        )

        service_request.transition_to(
            ServiceRequest.Status.SUBMITTED,
            changed_by=self.user,
        )

        service_request = RequestRoutingService.route_submitted(
            service_request=service_request,
            changed_by=self.user,
        )

        payment = PaymentService.create_payment(
            service_request=service_request,
        )

        PaymentService.mark_paid(
            payment=payment,
            reference_id="ROUTING-TEST-REF",
        )

        service_request.refresh_from_db()

        service_request.transition_to(
            ServiceRequest.Status.UNDER_REVIEW,
            changed_by=self.user,
        )

        service_request.transition_to(
            ServiceRequest.Status.NEEDS_CORRECTION,
            changed_by=self.user,
        )

        service_request.transition_to(
            ServiceRequest.Status.SUBMITTED,
            changed_by=self.user,
        )

        service_request = RequestRoutingService.route_submitted(
            service_request=service_request,
            changed_by=self.user,
        )

        self.assertEqual(
            service_request.status,
            ServiceRequest.Status.UNDER_REVIEW,
        )

        self.assertEqual(
            service_request.payments.count(),
            1,
        )