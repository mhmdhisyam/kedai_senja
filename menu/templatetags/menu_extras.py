from django import template

register = template.Library()


@register.filter
def rupiah(value):
    """25000 -> 'Rp 25.000'"""
    try:
        return "Rp " + f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return value
