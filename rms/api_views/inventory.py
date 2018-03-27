from ..models import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import reverse
from rms import models
from datetime import datetime
from django.utils.timezone import localtime, make_aware
from rms.exceptions import *


@login_required
def tag_search_view(request):
    if 'search' in request.GET:
        tags = Tag.objects.filter(name__contains=request.GET['search'])
        return_value = []
        for tag in tags:
            return_value.append(tag.name)
        return JsonResponse(return_value, status=200, safe=False)
    return HttpResponse('', 400)


@csrf_exempt
@login_required
def tag_add_view(request):
    if request.method == 'POST' and 'name' in request.POST:
        tag = Tag(name=request.POST['name'])
        tag.save()
        return HttpResponse('', 201)
    return HttpResponse('', 400)


@csrf_exempt
@login_required
def add_reservation_to_device(request, device_id):
    try:
        device = models.Device.objects.get(id=device_id)
        if request.POST and 'reservation' in request.POST and 'amount' in request.POST:
            try:
                reservation = models.Reservation.objects.get(id=request.POST.get('reservation'))
                device.add_to_reservation(reservation, int(request.POST['amount']))
                return HttpResponse('', status=200)
            except models.Reservation.DoesNotExist:
                pass
            except ReservationError as error:
                return JsonResponse(data=error.get_json_dir(), status=400, safe=False)
        return HttpResponse('', status=400)
    except models.Device.DoesNotExist:
        return HttpResponse('', status=404)


@csrf_exempt
@login_required
def edit_device_reservation(request, reservation_id, device_id):
    try:
        reservation = models.Reservation.objects.get(id=reservation_id)
        device = models.Device.objects.get(id=device_id)
        if request.method == 'POST' and 'amount' in request.POST:
            reservation_device_membership = reservation.reservationdevicemembership_set.get(device=device)
            new_ammount = int(request.POST['amount'])
            if new_ammount <= reservation_device_membership.amount:
                reservation_device_membership.amount = new_ammount
                reservation_device_membership.save()
                return HttpResponse('', status=200)
            else:
                try:
                    device.add_to_reservation(reservation, new_ammount-reservation_device_membership.amount)
                    return HttpResponse('', status=200)
                except ReservationError as error:
                    return JsonResponse(data=error.get_json_dir(), status=400, safe=False)
        else:
            return HttpResponse('POST required with field "amount"', status=404)
    except models.Reservation.DoesNotExist:
        return HttpResponse('Reservierung nicht gefunden', status=404)
    except models.Device.DoesNotExist:
        return HttpResponse('Gerät nicht gefunden', status=404)


@login_required
def device_reservations_json(request, device_id):
    try:
        device = models.Device.objects.get(id=device_id)
        reservations = []
        reservation_base = device.reservationdevicemembership_set
        if 'start' in request.GET:
            start = datetime.strptime(request.GET['start'], '%Y-%m-%d')
            reservation_base.filter(reservation__end_date__gte=start)
        if 'end' in request.GET:
            end = datetime.strptime(request.GET['end'], '%Y-%m-%d')
            reservation_base.filter(reservation__start_date__lte=end)
        for reservation in reservation_base.all():
            reservations.append({
                'start': localtime(reservation.reservation.start_date).isoformat(),
                'end': localtime(reservation.reservation.end_date).isoformat(),
                'url': reverse('reservation', kwargs={'reservation_id': reservation.reservation.id}),
                'title': '{} {}'.format(reservation.reservation.full_id, reservation.reservation.name),
                'description': 'Anzahl: {}'.format(reservation.amount),
            })
        return JsonResponse(reservations, status=200, safe=False)
    except models.Device.DoesNotExist:
        return HttpResponse('Device not found', status=404)


@login_required
def instance_reservations_json(request, instance_id):
    try:
        instance = models.Instance.objects.get(id=instance_id)
        reservations = []
        reservation_base = instance.reservation_set
        if 'start' in request.GET:
            start = datetime.strptime(request.GET['start'], '%Y-%m-%d')
            reservation_base.filter(end_date__gte=start)
        if 'end' in request.GET:
            end = datetime.strptime(request.GET['end'], '%Y-%m-%d')
            reservation_base.filter(start_date__lte=end)
        for reservation in reservation_base.all():
            reservations.append({
                'start': localtime(reservation.start_date).isoformat(),
                'end': localtime(reservation.end_date).isoformat(),
                'url': reverse('reservation', kwargs={'reservation_id': reservation.id}),
                'title': '{} {}'.format(reservation.full_id, reservation.name),
            })
        return JsonResponse(reservations, status=200, safe=False)
    except models.Instance.DoesNotExist:
        return HttpResponse('', status=404)


@csrf_exempt
@login_required
def add_instance_to_reservation(request, instance_id):
    try:
        instance = models.Instance.objects.get(id=instance_id)
        if request.method == 'POST' and 'reservation' in request.POST:
            try:
                reservation = models.Reservation.objects.get(id=int(request.POST['reservation']))
                instance.add_to_reservation(reservation)
                return HttpResponse('', status=200)
            except models.Reservation.DoesNotExist:
                return HttpResponse('Reservierung nicht gefunden.', status=404)
            except ReservationError as error:
                return JsonResponse(data=error.get_json_dir(), status=400, safe=False)
        else:
            return HttpResponse('POST required with field "reservation"', status=400)
    except models.Instance.DoesNotExist:
        return HttpResponse('Instanz nicht gefunden.', status=404)


@csrf_exempt
@login_required
def checkout_instance(request, reservation_id):
    try:
        reservation = models.Reservation.objects.get(id=reservation_id)
        if request.method == 'POST' and 'inventory_number' in request.POST:
            try:
                instance = models.Instance.objects.get(inventory_number=request.POST['inventory_number'])
                reservation.checkout_instance(instance)
                return HttpResponse('', status=200)
            except models.Instance.DoesNotExist:
                error = ReservationError('Es wurde kein Gerät mit der Inventarnummer "{}" gefunden'
                                         .format(request.POST['inventory_number']), set())
                return JsonResponse(data=error.get_json_dir(), status=404, safe=False)
            except CheckoutError as error:
                return JsonResponse(data=error.get_json_dir(), status=400, safe=False)
    except models.Reservation.DoesNotExist:
        return HttpResponse('Die Reservierung wurde nicht gefunden.', status=404)


@csrf_exempt
@login_required
def checkin_instance(request, reservation_id):
    try:
        reservation = models.Reservation.objects.get(id=reservation_id)
        if request.method == 'POST' and 'inventory_number' in request.POST:
            try:
                instance = models.Instance.objects.get(inventory_number=request.POST['inventory_number'])
                reservation.checkin_instance(instance)
                return HttpResponse('', status=200)
            except models.Instance.DoesNotExist:
                return HttpResponse('Es wurde kein gerät mit der Inventarnummer "{}" gefunden'
                                    .format(request.POST['inventory_number']), status=404)
            except CheckinError as error:
                return HttpResponse(str(error), status=400)
    except models.Reservation.DoesNotExist:
        return HttpResponse('Die Reservierung wurde nicht gefunden.', status=404)
