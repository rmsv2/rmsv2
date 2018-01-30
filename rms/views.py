from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from rms import forms
from . import models

# Create your views here.


@login_required()
def home_view(request):
    return render(request, 'home.html', context={'title': 'Home'})


@login_required()
def add_device_view(request):
    if request.method == 'POST':
        form = forms.DeviceForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            return redirect('home')
    else:
        form = forms.DeviceForm()
    return render(request, 'inventory/device_form.html', context={'form': form,
                                                                  'add': True,
                                                                  'title': 'Gerätetyp hinzufügen'})


@login_required()
def uncategorized_devices_view(request):
    return render(request, 'inventory/device_list.html', context={'devices': models.Device.untagged(),
                                                                  'title': 'Unkategorisierte Geräte'})


@login_required()
def delete_device_view(request, device_id):
    try:
        device = models.Device.objects.get(id=device_id)

        device.delete()

    except models.Device.DoesNotExist:
        pass

    if 'redirect' in request.GET:
        return redirect(request.GET['redirect'])
    elif 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect('home')
