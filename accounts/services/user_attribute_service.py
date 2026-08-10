from django.db import transaction
from django.utils import timezone

from accounts.models import UserAttribute


class UserAttributeService:

    @staticmethod
    @transaction.atomic
    def set_value(
        *,
        user,
        key: str,
        value,
    ) -> UserAttribute:
        key = key.strip()
        value = str(value).strip()

        if not key:
            raise ValueError("کلید اطلاعات الزامی است.")

        attribute = (
            UserAttribute.objects
            .select_for_update()
            .filter(
                user=user,
                key=key,
            )
            .first()
        )

        if attribute is None:
            return UserAttribute.objects.create(
                user=user,
                key=key,
                value=value,
            )

        if attribute.value != value:
            attribute.value = value

            # با تغییر مقدار، تأیید قبلی دیگر معتبر نیست.
            attribute.is_verified = False
            attribute.verified_at = None

            attribute.save(
                update_fields=[
                    "value",
                    "is_verified",
                    "verified_at",
                    "updated_at",
                ]
            )

        return attribute

    @staticmethod
    @transaction.atomic
    def verify(
        *,
        user,
        key: str,
    ) -> UserAttribute:
        attribute = (
            UserAttribute.objects
            .select_for_update()
            .get(
                user=user,
                key=key,
            )
        )

        attribute.is_verified = True
        attribute.verified_at = timezone.now()

        attribute.save(
            update_fields=[
                "is_verified",
                "verified_at",
                "updated_at",
            ]
        )

        return attribute

    @staticmethod
    def get_value(
        *,
        user,
        key: str,
        default=None,
    ):
        try:
            return UserAttribute.objects.get(
                user=user,
                key=key,
            ).value
        except UserAttribute.DoesNotExist:
            return default

    @staticmethod
    def get_user_data(*, user) -> dict:
        return dict(
            UserAttribute.objects
            .filter(user=user)
            .values_list("key", "value")
        )
    