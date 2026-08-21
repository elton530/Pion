import math

from django import template

register = template.Library()


@register.filter
def floor_stars(value):
    """Kthen numrin e plotë të yjeve (rrumbullakosur poshtë) për një vlerësim"""
    try:
        return int(math.floor(float(value)))
    except (TypeError, ValueError):
        return 0


@register.filter
def has_half_star(value):
    """True nëse vlerësimi ka gjysmë ylli (p.sh. 4.5)"""
    try:
        v = float(value)
        return abs(v - int(v)) >= 0.5
    except (TypeError, ValueError):
        return False
