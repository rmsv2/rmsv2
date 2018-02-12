from django import template

register = template.Library()


def price(value):
    return '{:.2f}'.format(value)


register.filter('price', price)
