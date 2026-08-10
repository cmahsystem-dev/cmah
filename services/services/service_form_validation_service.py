from datetime import date

from django.core.exceptions import ValidationError

from services.models import ServiceField


class ServiceFormValidationService:

    @staticmethod
    def validate(*, service, data: dict) -> dict:
        fields = (
            ServiceField.objects
            .filter(
                service=service,
                is_active=True,
            )
            .order_by("order", "id")
        )

        cleaned_data = {}
        errors = {}

        for field in fields:
            # فایل‌ها توسط RequestDocument / RequestFormService مدیریت می‌شوند.
            if field.field_type == ServiceField.FieldType.FILE:
                continue

            value = data.get(field.key)

            if isinstance(value, str):
                value = value.strip()

            is_empty = (
                value is None
                or value == ""
                or value == []
            )

            # Required
            if field.required and is_empty:
                errors[field.key] = "این فیلد الزامی است."
                continue

            # Optional empty field
            if is_empty:
                continue

            # NUMBER
            if field.field_type == ServiceField.FieldType.NUMBER:
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    errors[field.key] = "مقدار باید عدد باشد."
                    continue

            # DATE
            elif field.field_type == ServiceField.FieldType.DATE:
                if isinstance(value, date):
                    value = value.isoformat()

                elif isinstance(value, str):
                    try:
                        value = date.fromisoformat(value).isoformat()
                    except ValueError:
                        errors[field.key] = "تاریخ واردشده معتبر نیست."
                        continue

                else:
                    errors[field.key] = "تاریخ واردشده معتبر نیست."
                    continue

            # SELECT / RADIO
            elif field.field_type in {
                ServiceField.FieldType.SELECT,
                ServiceField.FieldType.RADIO,
            }:
                allowed_values = {
                    choice.get("value")
                    for choice in field.choices
                    if isinstance(choice, dict)
                    and choice.get("value") is not None
                }

                if value not in allowed_values:
                    errors[field.key] = "گزینه انتخاب‌شده معتبر نیست."
                    continue

            # CHECKBOX
            elif field.field_type == ServiceField.FieldType.CHECKBOX:
                if value not in {True, False}:
                    errors[field.key] = "مقدار چک‌باکس نامعتبر است."
                    continue

            cleaned_data[field.key] = value

        if errors:
            raise ValidationError(errors)

        return cleaned_data