import re

from django.core.exceptions import ValidationError


IRAN_MOBILE_REGEX = re.compile(r"^09\d{9}$")


def normalize_mobile(mobile: str) -> str:
    if not mobile:
        raise ValidationError("شماره موبایل الزامی است.")

    mobile = mobile.strip()
    mobile = mobile.replace(" ", "").replace("-", "")

    if mobile.startswith("+98"):
        mobile = "0" + mobile[3:]

    elif mobile.startswith("0098"):
        mobile = "0" + mobile[4:]

    elif mobile.startswith("98") and len(mobile) == 12:
        mobile = "0" + mobile[2:]

    if not IRAN_MOBILE_REGEX.fullmatch(mobile):
        raise ValidationError(
            "شماره موبایل معتبر نیست."
        )

    return mobile


def validate_mobile(mobile: str) -> None:
    normalize_mobile(mobile)