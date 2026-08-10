from accounts.services.user_attribute_service import UserAttributeService


class RequestDataService:

    @staticmethod
    def build_prefill(*, user, field_keys: list[str]) -> dict:
        user_data = UserAttributeService.get_user_data(
            user=user
        )

        return {
            key: user_data.get(key)
            for key in field_keys
            if key in user_data
        }

from django.db import transaction


class RequestDataService:

    @staticmethod
    def build_prefill(*, user, field_keys: list[str]) -> dict:
        user_data = UserAttributeService.get_user_data(
            user=user
        )

        return {
            key: user_data.get(key)
            for key in field_keys
            if key in user_data
        }

    @staticmethod
    @transaction.atomic
    def save_request_data(
        *,
        service_request,
        data: dict,
        reusable_fields: set[str] | None = None,
    ) -> None:
        reusable_fields = reusable_fields or set()

        clean_data = {}

        for key, value in data.items():
            if isinstance(value, str):
                value = value.strip()

            clean_data[key] = value

            if key in reusable_fields:
                UserAttributeService.set_value(
                    user=service_request.user,
                    key=key,
                    value=value,
                )

        service_request.request_data = clean_data
        service_request.save(
            update_fields=[
                "request_data",
                "updated_at",
            ]
        )