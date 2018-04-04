from django import template
from django.utils import timezone

register = template.Library()


@register.filter()
def actual(object):
    if object.__class__.__name__ == 'ManyRelatedManager' and str(object.model._meta) == 'rms.reservation':
        return object.filter(end_date__gte=timezone.now()).all()


@register.filter('order_by')
def order_by(object, order):
    return object.order_by(order)


@register.filter('all')
def all(object):
    return object.all()
