from django import template


register = template.Library()


@register.filter
def group_digits(value, size=4):
    if not value:
        return ""

    value = (
        str(value)
        .replace(" ", "")
        .replace("-", "")
    )

    size = int(size)

    return " ".join(
        value[index:index + size]
        for index in range(0, len(value), size)
    )