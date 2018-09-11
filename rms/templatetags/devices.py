from django import template
from ..models import Device, Warehouse

register = template.Library()


@register.filter('warehouses')
def warehouses(device: Device):
    return Warehouse.objects.filter(instance__in=device.instance_set.all())
