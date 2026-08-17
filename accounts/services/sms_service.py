import logging

from django.conf import settings
from ippanel import Client


logger = logging.getLogger(__name__)


class SMSServiceError(Exception):
    """Raised when sending an SMS fails."""
    pass


class SMSService:
    @staticmethod
    def send_otp(mobile: str, code: str) -> bool:
        if not mobile:
            raise ValueError("Mobile number is required.")

        if not code:
            raise ValueError("OTP code is required.")

        try:
            return SMSService._send_with_provider(
                mobile=mobile,
                code=code,
            )

        except Exception as exc:
            logger.exception(
                "SMS sending failed for mobile=%s",
                mobile,
            )

            raise SMSServiceError(
                "Unable to send SMS."
            ) from exc

    @staticmethod
    def _normalize_recipient(mobile: str) -> str:
        mobile = mobile.strip()

        if mobile.startswith("09"):
            return "98" + mobile[1:]

        if mobile.startswith("+98"):
            return mobile[1:]

        if mobile.startswith("98"):
            return mobile

        return mobile

    @staticmethod
    def _send_with_provider(
        mobile: str,
        code: str,
    ) -> bool:
        if not settings.IPPANEL_API_KEY:
            raise SMSServiceError(
                "IPPANEL_API_KEY is not configured."
            )

        if not settings.IPPANEL_PATTERN_CODE:
            raise SMSServiceError(
                "IPPANEL_PATTERN_CODE is not configured."
            )

        if not settings.IPPANEL_SENDER:
            raise SMSServiceError(
                "IPPANEL_SENDER is not configured."
            )

        client = Client(settings.IPPANEL_API_KEY)

        recipient = SMSService._normalize_recipient(mobile)

        response = client.send_pattern(
            pattern_code=settings.IPPANEL_PATTERN_CODE,
            sender=settings.IPPANEL_SENDER,
            recipient=recipient,
            params={
                "code": code,
            },
        )

        logger.info(
            "OTP SMS sent successfully | mobile=%s | response=%s",
            mobile,
            response,
        )

        return True
    