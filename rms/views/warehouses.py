from django.shortcuts import render, redirect, reverse
from ..models import Warehouse


def table_view(request):
    warehouses = Warehouse.objects.all()
    context = {
        'title': 'Lagerorte',
        'warehouses': warehouses
    }
    return render(request, 'warehouses/warehouses.html', context=context)
