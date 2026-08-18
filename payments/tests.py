from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from cases.models import ServiceRequest
from payments.models import (
    CardToCardDestination,
    Payment
)
from payments.services.payment_service import PaymentService
from services.models import Service
from cases.services.request_routing_service import RequestRoutingService
from payments.services.card_to_card_payment_service import (
    CardToCardPaymentService,
)
from django.core.files.uploadedfile import SimpleUploadedFile

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
            payment.method.code,
            "card_to_card",
        )

        self.assertIsNone(
            payment.gateway_provider,
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

    def test_create_payment_rejects_inactive_method(self):
        from django.core.exceptions import ValidationError

        from payments.models import PaymentMethod

        service_request = self._create_ready_request()

        PaymentMethod.objects.update_or_create(
            code="wallet",
            defaults={
                "title": "کیف پول",
                "is_active": False,
            },
        )

        with self.assertRaises(ValidationError):
            PaymentService.create_payment(
                service_request=service_request,
                method_code="wallet",
            )

        self.assertFalse(
            Payment.objects.filter(
                service_request=service_request,
                method__code="wallet",
            ).exists()
        )

    def test_create_payment_rejects_gateway_without_provider(self):
        from django.core.exceptions import ValidationError

        from payments.models import PaymentMethod

        service_request = self._create_ready_request()

        PaymentMethod.objects.update_or_create(
            code="gateway",
            defaults={
                "title": "درگاه بانکی",
                "is_active": True,
            },
        )

        with self.assertRaises(ValidationError):
            PaymentService.create_payment(
                service_request=service_request,
                method_code="gateway",
            )

        self.assertFalse(
            Payment.objects.filter(
                service_request=service_request,
                method__code="gateway",
            ).exists()
        )


    def test_create_payment_with_gateway_and_active_provider(self):
        from payments.models import GatewayProvider, PaymentMethod

        service_request = self._create_ready_request()

        PaymentMethod.objects.update_or_create(
            code="gateway",
            defaults={
                "title": "درگاه بانکی",
                "is_active": True,
            },
        )

        provider, _ = GatewayProvider.objects.update_or_create(
            code="mellat",
            defaults={
                "title": "بانک ملت",
                "is_active": True,
            },
        )

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="gateway",
            gateway_provider_code="mellat",
        )

        self.assertEqual(
            payment.method.code,
            "gateway",
        )

        self.assertEqual(
            payment.gateway_provider,
            provider,
        )

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

        self.assertEqual(
            payment.amount,
            service_request.amount,
        )


    def test_create_payment_rejects_provider_for_non_gateway_method(self):
        from django.core.exceptions import ValidationError

        from payments.models import GatewayProvider

        service_request = self._create_ready_request()

        GatewayProvider.objects.update_or_create(
            code="mellat",
            defaults={
                "title": "بانک ملت",
                "is_active": True,
            },
        )

        with self.assertRaises(ValidationError):
            PaymentService.create_payment(
                service_request=service_request,
                method_code="card_to_card",
                gateway_provider_code="mellat",
            )

        self.assertFalse(
            Payment.objects.filter(
                service_request=service_request,
            ).exists()
        )

    def test_create_payment_switches_pending_payment_method(self):
        from payments.models import PaymentMethod

        service_request = self._create_ready_request()

        PaymentMethod.objects.update_or_create(
            code="wallet",
            defaults={
                "title": "کیف پول",
                "is_active": True,
            },
        )

        first_payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        second_payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="wallet",
        )

        first_payment.refresh_from_db()

        self.assertEqual(
            first_payment.status,
            Payment.Status.CANCELLED,
        )

        self.assertEqual(
            first_payment.method.code,
            "card_to_card",
        )

        self.assertEqual(
            second_payment.status,
            Payment.Status.PENDING,
        )

        self.assertEqual(
            second_payment.method.code,
            "wallet",
        )

        self.assertNotEqual(
            first_payment.pk,
            second_payment.pk,
        )

        self.assertEqual(
            Payment.objects.filter(
                service_request=service_request,
                status=Payment.Status.PENDING,
            ).count(),
            1,
        )

    def test_create_payment_rejects_when_payment_awaits_verification(self):
        from django.core.exceptions import ValidationError

        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        payment.status = Payment.Status.AWAITING_VERIFICATION
        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        with self.assertRaises(ValidationError):
            PaymentService.create_payment(
                service_request=service_request,
                method_code="card_to_card",
            )

        self.assertEqual(
            Payment.objects.filter(
                service_request=service_request,
            ).count(),
            1,
        )

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.AWAITING_VERIFICATION,
        )

    def test_submit_card_to_card_payment_successfully(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        detail = CardToCardPaymentService.submit_payment(
            payment=payment,
            payer_reference="123456789",
        )

        payment.refresh_from_db()
        detail.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.AWAITING_VERIFICATION,
        )

        self.assertEqual(
            detail.payment,
            payment,
        )

        self.assertEqual(
            detail.payer_reference,
            "123456789",
        )

        self.assertIsNotNone(
            detail.submitted_at,
        )

        self.assertFalse(
            bool(detail.receipt),
        )

        self.assertIsNone(
            detail.verified_by,
        )

        self.assertIsNone(
            detail.verified_at,
        )

        self.assertEqual(
            detail.rejection_reason,
            "",
        )

    def test_submit_card_to_card_rejects_non_card_to_card_payment(self):
        from django.core.exceptions import ValidationError

        from payments.models import PaymentMethod

        service_request = self._create_ready_request()

        PaymentMethod.objects.update_or_create(
            code="wallet",
            defaults={
                "title": "کیف پول",
                "is_active": True,
            },
        )

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="wallet",
        )

        with self.assertRaises(ValidationError):
            CardToCardPaymentService.submit_payment(
                payment=payment,
                payer_reference="123456789",
            )

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

        self.assertFalse(
            hasattr(payment, "card_to_card_detail"),
        )

    def test_submit_card_to_card_rejects_non_pending_payment(self):
        from django.core.exceptions import ValidationError

        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        detail = CardToCardPaymentService.submit_payment(
            payment=payment,
            payer_reference="123456789",
        )

        with self.assertRaises(ValidationError):
            CardToCardPaymentService.submit_payment(
                payment=payment,
                payer_reference="987654321",
            )

        payment.refresh_from_db()
        detail.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.AWAITING_VERIFICATION,
        )

        self.assertEqual(
            detail.payer_reference,
            "123456789",
        )

    def test_submit_card_to_card_requires_payer_reference(self):
        from django.core.exceptions import ValidationError

        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        with self.assertRaises(ValidationError):
            CardToCardPaymentService.submit_payment(
                payment=payment,
                payer_reference="   ",
            )

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

        self.assertFalse(
            hasattr(payment, "card_to_card_detail"),
        )

    def test_submit_card_to_card_saves_receipt(self):
        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        receipt = SimpleUploadedFile(
            "receipt.jpg",
            b"fake-receipt-content",
            content_type="image/jpeg",
        )

        detail = CardToCardPaymentService.submit_payment(
            payment=payment,
            payer_reference="123456789",
            receipt=receipt,
        )

        detail.refresh_from_db()
        payment.refresh_from_db()

        self.assertTrue(
            bool(detail.receipt),
        )

        self.assertEqual(
            payment.status,
            Payment.Status.AWAITING_VERIFICATION,
        )

    def test_prepare_card_to_card_payment_uses_active_destination(self):
        service_request = self._create_ready_request()

        destination = CardToCardDestination.objects.create(
            title="کارت اصلی CMAH",
            card_number="6037991234567890",
            iban="IR120000000000000000000000",
            account_holder="CMAH",
            bank_name="بانک تست",
            is_active=True,
            priority=10,
        )

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        detail = CardToCardPaymentService.prepare_payment(
            payment=payment,
        )

        self.assertEqual(
            detail.destination,
            destination,
        )

        self.assertEqual(
            detail.destination_title,
            destination.title,
        )

        self.assertEqual(
            detail.destination_card_number,
            destination.card_number,
        )

        self.assertEqual(
            detail.destination_iban,
            destination.iban,
        )

        self.assertEqual(
            detail.destination_account_holder,
            destination.account_holder,
        )

        self.assertEqual(
            detail.destination_bank_name,
            destination.bank_name,
        )

    def test_prepare_card_to_card_payment_preserves_snapshot(self):
        service_request = self._create_ready_request()

        destination = CardToCardDestination.objects.create(
            title="کارت اصلی CMAH",
            card_number="6037991234567890",
            account_holder="CMAH",
            bank_name="بانک تست",
            is_active=True,
            priority=10,
        )

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        detail = CardToCardPaymentService.prepare_payment(
            payment=payment,
        )

        original_card_number = (
            detail.destination_card_number
        )

        destination.card_number = "5892109876543210"
        destination.save(
            update_fields=[
                "card_number",
                "updated_at",
            ]
        )

        detail = CardToCardPaymentService.prepare_payment(
            payment=payment,
        )

        detail.refresh_from_db()

        self.assertEqual(
            detail.destination_card_number,
            original_card_number,
        )

        self.assertNotEqual(
            detail.destination_card_number,
            destination.card_number,
        )

    def test_prepare_card_to_card_payment_requires_active_destination(self):
        from django.core.exceptions import ValidationError

        service_request = self._create_ready_request()

        CardToCardDestination.objects.create(
            title="کارت غیرفعال",
            card_number="6037991234567890",
            account_holder="CMAH",
            bank_name="بانک تست",
            is_active=False,
            priority=10,
        )

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        with self.assertRaises(ValidationError):
            CardToCardPaymentService.prepare_payment(
                payment=payment,
            )

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )
        