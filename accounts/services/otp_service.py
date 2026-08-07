import secrets
from datetime import timedelta
from secrets import compare_digest
from accounts.utils.mobile import normalize_mobile
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import OTPCode, User
from accounts.services.sms_service import SMSService


class OTPService:
    MAX_ATTEMPTS = settings.OTP_MAX_ATTEMPTS

    @staticmethod
    @transaction.atomic
    def generate(user: User) -> OTPCode:
        code = f"{secrets.randbelow(1_000_000):06d}"

        expires_at = timezone.now() + timedelta(
            minutes=settings.OTP_EXPIRY_MINUTES
        )

        OTPCode.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).update(is_used=True)

        return OTPCode.objects.create(
            user=user,
            code=code,
            expires_at=expires_at,
        )

    @staticmethod
    def request_otp(mobile: str) -> OTPCode:
        mobile = normalize_mobile(mobile)

        user, _ = User.objects.get_or_create(
            mobile=mobile,
        )

        otp = OTPService.generate(user)

        SMSService.send_otp(
            mobile=user.mobile,
            code=otp.code,
        )

        return otp

    @staticmethod
    @transaction.atomic
    def verify(user: User, code: str) -> bool:
        otp = (
            OTPCode.objects
            .select_for_update()
            .filter(
                user=user,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .first()
        )

        if otp is None:
            return False

        if otp.attempts >= OTPService.MAX_ATTEMPTS:
            otp.is_used = True
            otp.save(update_fields=["is_used"])
            return False

        if not compare_digest(otp.code, code):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            return False

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        if not user.is_mobile_verified:
            user.is_mobile_verified = True
            user.save(update_fields=["is_mobile_verified"])

        return True