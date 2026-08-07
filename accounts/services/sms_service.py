import logging

from django.conf import settings


logger = logging.getLogger(__name__)


class SMSServiceError(Exception):
    """Raised when sending an SMS fails."""
    pass


class SMSService:
    @staticmethod
    def send_otp(mobile: str, code: str) -> bool:
        """
        Send an OTP code to the given mobile number.

        In development mode, if no SMS provider is configured,
        the OTP is logged to the console instead of being sent.
        """

        if not mobile:
            raise ValueError("Mobile number is required.")

        if not code:
            raise ValueError("OTP code is required.")

        message = SMSService.build_otp_message(code)

        if settings.DEBUG:
            logger.info(
                "Development OTP | mobile=%s | code=%s",
                mobile,
                code,
            )
            print(f"[SMS DEBUG] {mobile} -> {message}")
            return True

        try:
            return SMSService._send_with_provider(
                mobile=mobile,
                message=message,
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
    def build_otp_message(code: str) -> str:
        return (
            f"کد ورود شما به سی ماه:\n"
            f"{code}\n"
            f"این کد را در اختیار دیگران قرار ندهید."
        )

    @staticmethod
    def _send_with_provider(
        mobile: str,
        message: str,
    ) -> bool:
        """
        Production SMS provider integration.

        A real provider such as Kavenegar, IPPanel,
        Melipayamak, etc. will be connected here.
        """

        raise NotImplementedError(
            "SMS provider is not configured."
        )