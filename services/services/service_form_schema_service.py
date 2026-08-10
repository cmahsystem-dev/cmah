from services.models import ServiceField


class ServiceFormSchemaService:

    @staticmethod
    def build(*, service) -> list[dict]:
        fields = (
            ServiceField.objects
            .filter(
                service=service,
                is_active=True,
            )
            .order_by("order", "id")
        )

        return [
            {
                "key": field.key,
                "label": field.label,
                "type": field.field_type,
                "required": field.required,
                "reusable": field.reusable,
                "help_text": field.help_text,
                "placeholder": field.placeholder,
                "choices": field.choices,
            }
            for field in fields
        ]
    