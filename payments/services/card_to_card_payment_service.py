from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from cases.services.request_timeline_service import RequestTimelineService
from payments.models import (
    CardToCardDestination,
    CardToCardPaymentDetail,
    Payment,
)
from django.conf import settings
from payments.services.payment_service import PaymentService
from accounts.models import User

class CardToCardPaymentService:

    @staticmethod
    @transaction.atomic
    def submit_payment(
        *,
        payment: Payment,
        payer_reference: str,
        receipt=None,
    ) -> CardToCardPaymentDetail:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related(
                "method",
                "service_request",
            )
            .get(pk=payment.pk)
        )

        if payment.method.code != "card_to_card":
            raise ValidationError(
                "این پرداخت از نوع کارت‌به‌کارت نیست."
            )

        if payment.status != Payment.Status.PENDING:
            raise ValidationError(
                "این پرداخت در وضعیت فعلی قابل ثبت نیست."
            )

        payer_reference = (payer_reference or "").strip()

        if not payer_reference:
            raise ValidationError(
                "شماره پیگیری پرداخت الزامی است."
            )

        detail, _ = (
            CardToCardPaymentDetail.objects
            .select_for_update()
            .get_or_create(
                payment=payment,
            )
        )

        # در وضعیت PENDING ممکن است کاربر قبل از ارسال نهایی
        # اطلاعات را دوباره ثبت کند.
        detail.payer_reference = payer_reference

        if receipt is not None:
            detail.receipt = receipt

        detail.submitted_at = timezone.now()

        # اگر Detail قبلاً داده بررسی داشته باشد،
        # submit جدید نباید آن اطلاعات را حمل کند.
        detail.verified_by = None
        detail.verified_at = None
        detail.rejection_reason = ""

        detail.save()

        payment.status = Payment.Status.AWAITING_VERIFICATION

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        RequestTimelineService.record(
            service_request=payment.service_request,
            event_type="payment",
            title="اطلاعات پرداخت کارت‌به‌کارت ثبت شد.",
            metadata={
                "payment_id": payment.pk,
                "method": payment.method.code,
                "payer_reference": detail.payer_reference,
                "has_receipt": bool(detail.receipt),
            },
        )

        return detail

    @staticmethod
    @transaction.atomic
    def approve(
        *,
        payment: Payment,
        verified_by,
    ) -> CardToCardPaymentDetail:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related(
                "method",
                "service_request",
            )
            .get(pk=payment.pk)
        )

        if payment.method.code != "card_to_card":
            raise ValidationError(
                "این پرداخت از نوع کارت‌به‌کارت نیست."
            )

        if payment.status == Payment.Status.PAID:
            return payment.card_to_card_detail

        if payment.status != Payment.Status.AWAITING_VERIFICATION:
            raise ValidationError(
                "این پرداخت در انتظار تأیید نیست."
            )

        if verified_by is None:
            raise ValidationError(
                "کاربر تأییدکننده الزامی است."
            )

        try:
            detail = (
                CardToCardPaymentDetail.objects
                .select_for_update()
                .get(payment=payment)
            )
        except CardToCardPaymentDetail.DoesNotExist:
            raise ValidationError(
                "اطلاعات پرداخت کارت‌به‌کارت یافت نشد."
            )

        detail.verified_by = verified_by
        detail.verified_at = timezone.now()
        detail.rejection_reason = ""

        detail.save(
            update_fields=[
                "verified_by",
                "verified_at",
                "rejection_reason",
                "updated_at",
            ]
        )

        PaymentService.mark_paid(
            payment=payment,
            reference_id=detail.payer_reference,
        )

        return detail

    @staticmethod
    @transaction.atomic
    def reject(
        *,
        payment: Payment,
        verified_by,
        rejection_reason: str,
    ) -> CardToCardPaymentDetail:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related(
                "method",
                "service_request",
            )
            .get(pk=payment.pk)
        )

        if payment.method.code != "card_to_card":
            raise ValidationError(
                "این پرداخت از نوع کارت‌به‌کارت نیست."
            )

        if payment.status != Payment.Status.AWAITING_VERIFICATION:
            raise ValidationError(
                "این پرداخت در انتظار تأیید نیست."
            )

        if verified_by is None:
            raise ValidationError(
                "کاربر بررسی‌کننده الزامی است."
            )

        rejection_reason = (rejection_reason or "").strip()

        if not rejection_reason:
            raise ValidationError(
                "دلیل رد پرداخت الزامی است."
            )

        try:
            detail = (
                CardToCardPaymentDetail.objects
                .select_for_update()
                .get(payment=payment)
            )
        except CardToCardPaymentDetail.DoesNotExist:
            raise ValidationError(
                "اطلاعات پرداخت کارت‌به‌کارت یافت نشد."
            )

        detail.verified_by = verified_by
        detail.verified_at = timezone.now()
        detail.rejection_reason = rejection_reason

        detail.save(
            update_fields=[
                "verified_by",
                "verified_at",
                "rejection_reason",
                "updated_at",
            ]
        )

        PaymentService.mark_failed(
            payment=payment,
        )

        return detail

    def test_approve_card_to_card_payment_successfully(self):
        from accounts.models import User

        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        CardToCardPaymentService.submit_payment(
            payment=payment,
            payer_reference="123456789",
        )

        operator = User.objects.create_user(
            mobile="09120000001",
        )

        detail = CardToCardPaymentService.approve(
            payment=payment,
            verified_by=operator,
        )

        payment.refresh_from_db()
        detail.refresh_from_db()
        service_request.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.PAID,
        )

        self.assertEqual(
            payment.reference_id,
            "123456789",
        )

        self.assertIsNotNone(
            payment.paid_at,
        )

        self.assertEqual(
            detail.verified_by,
            operator,
        )

        self.assertIsNotNone(
            detail.verified_at,
        )

        self.assertEqual(
            detail.rejection_reason,
            "",
        )

        self.assertEqual(
            service_request.status,
            ServiceRequest.Status.PAID,
        )


    def test_approve_card_to_card_rejects_non_awaiting_payment(self):
        from accounts.models import User
        from django.core.exceptions import ValidationError

        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        operator = User.objects.create_user(
            mobile="09120000002",
        )

        with self.assertRaises(ValidationError):
            CardToCardPaymentService.approve(
                payment=payment,
                verified_by=operator,
            )

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )   

    def test_approve_card_to_card_requires_verifier(self):
        from django.core.exceptions import ValidationError

        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        CardToCardPaymentService.submit_payment(
            payment=payment,
            payer_reference="123456789",
        )

        with self.assertRaises(ValidationError):
            CardToCardPaymentService.approve(
                payment=payment,
                verified_by=None,
            )

    def test_reject_card_to_card_payment_successfully(self):
        from accounts.models import User

        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        CardToCardPaymentService.submit_payment(
            payment=payment,
            payer_reference="123456789",
        )

        operator = User.objects.create_user(
            mobile="09120000003",
        )

        detail = CardToCardPaymentService.reject(
            payment=payment,
            verified_by=operator,
            rejection_reason="رسید پرداخت قابل تأیید نیست.",
        )

        payment.refresh_from_db()
        detail.refresh_from_db()
        service_request.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.FAILED,
        )

        self.assertEqual(
            detail.verified_by,
            operator,
        )

        self.assertIsNotNone(
            detail.verified_at,
        )

        self.assertEqual(
            detail.rejection_reason,
            "رسید پرداخت قابل تأیید نیست.",
        )

        # رد Payment نباید ServiceRequest را از
        # READY_FOR_PAYMENT خارج کند.
        self.assertEqual(
            service_request.status,
            ServiceRequest.Status.READY_FOR_PAYMENT,
        )

    def test_reject_card_to_card_requires_reason(self):
        from accounts.models import User
        from django.core.exceptions import ValidationError

        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        CardToCardPaymentService.submit_payment(
            payment=payment,
            payer_reference="123456789",
        )

        operator = User.objects.create_user(
            mobile="09120000004",
        )

        with self.assertRaises(ValidationError):
            CardToCardPaymentService.reject(
                payment=payment,
                verified_by=operator,
                rejection_reason="   ",
            )

    def test_reject_card_to_card_requires_verifier(self):
        from django.core.exceptions import ValidationError

        service_request = self._create_ready_request()

        payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        CardToCardPaymentService.submit_payment(
            payment=payment,
            payer_reference="123456789",
        )

        with self.assertRaises(ValidationError):
            CardToCardPaymentService.reject(
                payment=payment,
                verified_by=None,
                rejection_reason="رسید نامعتبر است.",
            )

    def test_card_to_card_can_retry_after_rejection(self):
        from accounts.models import User

        service_request = self._create_ready_request()

        first_payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        CardToCardPaymentService.submit_payment(
            payment=first_payment,
            payer_reference="111111111",
        )

        operator = User.objects.create_user(
            mobile="09120000005",
        )

        CardToCardPaymentService.reject(
            payment=first_payment,
            verified_by=operator,
            rejection_reason="پرداخت تأیید نشد.",
        )

        second_payment = PaymentService.create_payment(
            service_request=service_request,
            method_code="card_to_card",
        )

        first_payment.refresh_from_db()

        self.assertEqual(
            first_payment.status,
            Payment.Status.FAILED,
        )

        self.assertEqual(
            second_payment.status,
            Payment.Status.PENDING,
        )

        self.assertEqual(
            second_payment.method.code,
            "card_to_card",
        )

        self.assertNotEqual(
            first_payment.pk,
            second_payment.pk,
        )

    @staticmethod
    @transaction.atomic
    def prepare_payment(
        *,
        payment: Payment,
    ) -> CardToCardPaymentDetail:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related(
                "method",
                "service_request",
            )
            .get(pk=payment.pk)
        )

        if payment.method.code != "card_to_card":
            raise ValidationError(
                "این پرداخت از نوع کارت‌به‌کارت نیست."
            )

        if payment.status != Payment.Status.PENDING:
            raise ValidationError(
                "این پرداخت در وضعیت فعلی قابل آماده‌سازی نیست."
            )

        destination = (
            CardToCardDestination.objects
            .filter(
                is_active=True,
            )
            .order_by(
                "priority",
                "id",
            )
            .first()
        )

        if destination is None:
            raise ValidationError(
                "هیچ کارت مقصد فعالی برای پرداخت کارت‌به‌کارت تعریف نشده است."
            )

        detail, created = (
            CardToCardPaymentDetail.objects
            .select_for_update()
            .get_or_create(
                payment=payment,
            )
        )

        if created or detail.destination_id is None:
            detail.destination = destination

            detail.destination_title = (
                destination.title
            )

            detail.destination_card_number = (
                destination.card_number
            )

            detail.destination_iban = (
                destination.iban
            )

            detail.destination_account_holder = (
                destination.account_holder
            )

            detail.destination_bank_name = (
                destination.bank_name
            )

            detail.save(
                update_fields=[
                    "destination",
                    "destination_title",
                    "destination_card_number",
                    "destination_iban",
                    "destination_account_holder",
                    "destination_bank_name",
                    "updated_at",
                ]
            )

        return detail