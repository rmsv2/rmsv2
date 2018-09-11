from django.shortcuts import render, redirect, reverse
from ..models import Warehouse
from ..forms import WarehouseForm, AddressForm


def table_view(request):
    warehouses = Warehouse.objects.all()
    context = {
        'title': 'Lagerorte',
        'warehouses': warehouses
    }
    return render(request, 'warehouses/warehouses.html', context=context)


def create_warehouse(request):
    if request.method == 'POST':
        warehouse_form = WarehouseForm(request.POST, prefix='warehouse')
        address_form = AddressForm(request.POST, prefix='address')
        if address_form.is_valid() and warehouse_form.is_valid():
            warehouse = warehouse_form.save(commit=False)
            address = address_form.save(commit=False)
            address.save()
            warehouse.address = address
            warehouse.save()
            return redirect('warehouses')
    else:
        warehouse_form = WarehouseForm(prefix='warehouse')
        address_form = AddressForm(prefix='address')
    return render(request, 'warehouses/warehouse_form.html', context={'title': 'Lagerort anlegen', 'type': 'new',
                                                                      'warehouse_form': warehouse_form,
                                                                      'address_form': address_form})


def delete_warehouse(request, warehouse_id):
    if request.method == 'POST':
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
            warehouse.delete()
        except Warehouse.DoesNotExist:
            pass
    return redirect('warehouses')


def edit_warehouse(request, warehouse_id):
    try:
        warehouse = Warehouse.objects.get(id=warehouse_id)
        if request.method == 'POST':
            warehouse_form = WarehouseForm(request.POST, instance=warehouse, prefix='warehouse')
            address_form = AddressForm(request.POST, instance=warehouse.address, prefix='address')
            if warehouse_form.is_valid() and address_form.is_valid():
                warehouse_form.save(commit=True)
                address_form.save(commit=True)
                return redirect('warehouses')
        else:
            warehouse_form = WarehouseForm(instance=warehouse, prefix='warehouse')
            address_form = AddressForm(instance=warehouse.address, prefix='address')
        return render(request, 'warehouses/warehouse_form.html', context={'title': 'Lagerort bearbeiten',
                                                                          'type': 'edit',
                                                                          'warehouse_form': warehouse_form,
                                                                          'address_form': address_form,
                                                                          'warehouse': warehouse})
    except Warehouse.DoesNotExist:
        return redirect('warehouses')
