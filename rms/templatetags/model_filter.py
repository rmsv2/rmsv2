from django import template
from django.utils import timezone

register = template.Library()


@register.filter()
def actual(object):
    if object.__class__.__name__ == 'ManyRelatedManager' and str(object.model._meta) == 'rms.reservation':
        return object.filter(start_date__gte=timezone.now()).all()
