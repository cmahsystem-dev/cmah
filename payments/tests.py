from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from cases.models import ServiceRequest
from payments.models import Payment
from payments.services.payment_service import PaymentService
from services.models import Service
from cases.services.request_routing_service import RequestRoutingService


class PaymentServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            mobile="09121111111",
        )

        self.service = Service.objects.create(
            title="خدمت تست پرداخت",
            slug="payment-test-service",
        )

    def _create_ready_request(
        self,
        *,
        amount=250_000,
    ):
        service_request = ServiceRequest.objects.create(
            user=self.user,
            service=self.service,
            amount=amount,
        )

        service_request.transition_to(
            ServiceRequest.Status.SUBMITTED,
            changed_by=self.user,
        )

        service_request.transition_to(
            ServiceRequest.Status.READY_FOR_PAYMENT,
            changed_by=self.user,
        )

        return service_request

    # --------------------------------------------------
    # CREATE PAYMENT
    # --------------------------------------------------

    def test_create_payment_creates_pending_payment(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
        )

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

        self.assertEqual(
            payment.amount,
            service_request.amount,
        )

        self.assertEqual(
            payment.gateway,
            Payment.Gateway.MANUAL,
        )

    def test_create_payment_reuses_existing_pending_payment(self):
        service_request = self._create_ready_request()

        payment1 = PaymentService.create_payment(
            service_request=service_request,
        )

        payment2 = PaymentService.create_payment(
            service_request=service_request,
        )

        self.assertEqual(
            payment1.pk,
            payment2.pk,
        )

        self.assertEqual(
            Payment.objects.filter(
                service_request=service_request,
            ).count(),
            1,
        )

    def test_payment_cannot_be_created_for_wrong_request_status(self):
        service_request = ServiceRequest.objects.create(
            user=self.user,
            service=self.service,
            amount=250_000,
        )

        with self.assertRaises(ValidationError):
            PaymentService.create_payment(
                service_request=service_request,
            )

    def test_payment_cannot_be_created_for_free_request(self):
        service_request = self._create_ready_request(
            amount=0,
        )

        with self.assertRaises(ValidationError):
            PaymentService.create_payment(
                service_request=service_request,
            )

        self.assertEqual(
            Payment.objects.filter(
                service_request=service_request,
            ).count(),
            0,
        )

    # --------------------------------------------------
    # PAID
    # --------------------------------------------------

    def test_mark_paid_updates_payment_and_request(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
        )

        payment = PaymentService.mark_paid(
            payment=payment,
            reference_id="REF-001",
            authority="AUTH-001",
        )

        service_request.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.PAID,
        )

        self.assertEqual(
            payment.reference_id,
            "REF-001",
        )

        self.assertEqual(
            payment.authority,
            "AUTH-001",
        )

        self.assertIsNotNone(
            payment.paid_at,
        )

        self.assertEqual(
            service_request.status,
            ServiceRequest.Status.PAID,
        )

    def test_mark_paid_requires_reference_id(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
        )

        with self.assertRaises(ValidationError):
            PaymentService.mark_paid(
                payment=payment,
                reference_id="",
            )

    def test_paid_callback_is_idempotent(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
        )

        payment1 = PaymentService.mark_paid(
            payment=payment,
            reference_id="REF-001",
            authority="AUTH-001",
        )

        payment2 = PaymentService.mark_paid(
            payment=payment1,
            reference_id="REF-001",
            authority="AUTH-001",
        )

        self.assertEqual(
            payment1.pk,
            payment2.pk,
        )

        self.assertEqual(
            Payment.objects.filter(
                service_request=service_request,
            ).count(),
            1,
        )

    def test_paid_request_cannot_create_new_payment(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
        )

        PaymentService.mark_paid(
            payment=payment,
            reference_id="REF-001",
        )

        with self.assertRaises(ValidationError):
            PaymentService.create_payment(
                service_request=service_request,
            )

    # --------------------------------------------------
    # FAILED
    # --------------------------------------------------

    def test_mark_failed_keeps_request_ready_for_payment(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
        )

        payment = PaymentService.mark_failed(
            payment=payment,
        )

        service_request.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.FAILED,
        )

        self.assertEqual(
            service_request.status,
            ServiceRequest.Status.READY_FOR_PAYMENT,
        )

    def test_failed_payment_allows_retry(self):
        service_request = self._create_ready_request()

        payment1 = PaymentService.create_payment(
            service_request=service_request,
        )

        PaymentService.mark_failed(
            payment=payment1,
        )

        payment2 = PaymentService.create_payment(
            service_request=service_request,
        )

        self.assertNotEqual(
            payment1.pk,
            payment2.pk,
        )

        self.assertEqual(
            payment2.status,
            Payment.Status.PENDING,
        )

        self.assertEqual(
            Payment.objects.filter(
                service_request=service_request,
            ).count(),
            2,
        )

    # --------------------------------------------------
    # CANCELLED
    # --------------------------------------------------

    def test_cancel_keeps_request_ready_for_payment(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
        )

        payment = PaymentService.cancel(
            payment=payment,
        )

        service_request.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.CANCELLED,
        )

        self.assertEqual(
            service_request.status,
            ServiceRequest.Status.READY_FOR_PAYMENT,
        )

    def test_cancelled_payment_allows_retry(self):
        service_request = self._create_ready_request()

        payment1 = PaymentService.create_payment(
            service_request=service_request,
        )

        PaymentService.cancel(
            payment=payment1,
        )

        payment2 = PaymentService.create_payment(
            service_request=service_request,
        )

        self.assertNotEqual(
            payment1.pk,
            payment2.pk,
        )

        self.assertEqual(
            payment2.status,
            Payment.Status.PENDING,
        )

        self.assertEqual(
            Payment.objects.filter(
                service_request=service_request,
            ).count(),
            2,
        )

    # --------------------------------------------------
    # TIMELINE
    # --------------------------------------------------

    def test_payment_creation_adds_timeline_event(self):
        service_request = self._create_ready_request()

        PaymentService.create_payment(
            service_request=service_request,
        )

        self.assertTrue(
            service_request.timeline.filter(
                event_type="payment",
                title="فرآیند پرداخت ایجاد شد.",
            ).exists()
        )

    def test_successful_payment_adds_timeline_event(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
        )

        PaymentService.mark_paid(
            payment=payment,
            reference_id="REF-001",
        )

        self.assertTrue(
            service_request.timeline.filter(
                event_type="payment",
                title="پرداخت با موفقیت انجام شد.",
            ).exists()
        )