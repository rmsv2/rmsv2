from django.db import models
from django.contrib.auth import models as auth_models
from djmoney.models.fields import MoneyField
import string
import random
import os
from rmsv2.settings import BASE_DIR, COMPANY_SHORT
from django.db.models import Q
from rms.exceptions import *
from django.utils import timezone

# Create your models here.


def get_device_image_upload_path(instance, orig_filename):
    while True:
        filename = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
        path = os.path.join('static/uploads/devices/', str(instance.id), filename)
        if not os.path.isfile(os.path.join(BASE_DIR, path)):
            break
    return path


class User(auth_models.User):

    class Meta:
        proxy = True
        permissions = (('view_user', 'Can view user'),)


class Group(auth_models.Group):

    class Meta:
        proxy = True
        permissions = (('view_group', 'Can view group'),)


class Tag(models.Model):
    name = models.CharField('Name', max_length=200, unique=True, primary_key=True)


class Category(models.Model):

    class Meta:
        permissions = (('view_category', 'Can view category'),)

    name = models.CharField('Name', max_length=200)
    top_category = models.ForeignKey('Category', on_delete=models.PROTECT, null=True, blank=True, verbose_name='Übergeordnete Kategorie')

    def __str__(self):
        return self.name

    def sub_categories_sorted_by_name(self):
        return Category.objects.filter(top_category=self).order_by('name')


class Device(models.Model):

    class Meta:
        permissions = (('view_device', 'Can view device'),)

    name = models.CharField('Name', max_length=100)
    picture = models.ImageField('Bild', upload_to=get_device_image_upload_path, blank=True, null=True, default=None)
    model_number = models.CharField('Modell Nummer', max_length=100)
    vendor = models.CharField('Hersteller', max_length=300, default='')
    description = models.TextField('Beschreibung', null=True, blank=True)
    price_new = MoneyField('Neupreis', decimal_places=2, max_digits=20, default_currency='EUR')
    price_rental = MoneyField('Vermietpreis', decimal_places=2, max_digits=20, default_currency='EUR')
    tags = models.ManyToManyField(Tag, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, verbose_name='Kategorie', blank=True)
    active = models.BooleanField(default=True)

    @classmethod
    def uncategorized(cls):
        return cls.objects.filter(category=None).filter(active=True)

    def __str__(self):
        return '{} ({})'.format(self.name, self.vendor)

    def available_count(self, start, end):
        available = 0
        collisions = set()
        for instance in self.instance_set.all():
            is_available, instance_collisions = instance.is_available(start, end)
            if is_available:
                available += 1
            else:
                collisions = collisions.union(instance_collisions)
        colliding_reservations = self.reservationdevicemembership_set.filter(
            (Q(reservation__start_date__gte=start) & Q(reservation__end_date__lt=end)) |
            (Q(reservation__end_date__gt=start) & Q(reservation__end_date__lte=end)) |
            (Q(reservation__start_date__lte=start) & Q(reservation__end_date__gte=end))
        )
        colliding_reservations_count = colliding_reservations.aggregate(models.Sum('amount'))['amount__sum']
        for reservation_relation in colliding_reservations:
            collisions.add(reservation_relation.reservation)
        if colliding_reservations_count is not None:
            available -= colliding_reservations_count
        return available, collisions

    def add_to_reservation(self, reservation, amount):
        available, collisions = self.available_count(reservation.start_date, reservation.end_date)
        if available < amount:
            raise ReservationError('Es sind nicht genug Geräte zur ausgewählten Zeit verfügbar.', collisions)
        try:
            reservationdevice_membership = reservation.reservationdevicemembership_set.get(device=self)
            reservationdevice_membership.amount += amount
            reservationdevice_membership.save()
        except ReservationDeviceMembership.DoesNotExist:
            ReservationDeviceMembership.objects.create(reservation=reservation, device=self, amount=amount)

    def instances_to_checkout(self, reservation):
        reservation_relation = self.reservationdevicemembership_set.objects.get(reservation=reservation)
        instances = []
        for instance in self.instance_set.all():
            is_available, collisions = instance.is_available(reservation_relation.reservation.start_date,
                                                             reservation_relation.reservation.end_date)
            if is_available:
                instances.append(instance)
        return instances


class Instance(models.Model):

    class Meta:
        permissions = (('view_unrentable', 'Can view unrentable inventory'),
                       ('view_instance', 'Can view instance'),)

    serial_number = models.CharField('Seriennummer', max_length=200, null=True, blank=True)
    inventory_number = models.CharField('Inventarnummer', max_length=200, unique=True)
    identificial_description = models.TextField('Identifikations- beschreibung', null=True, blank=True)
    broken = models.BooleanField('Defekt?')
    rentable = models.BooleanField('Ausleihbar', default=False)
    device = models.ForeignKey(Device, on_delete=models.PROTECT, verbose_name='Gerätetyp')
    tags = models.ManyToManyField(Tag, blank=True)
    active = models.BooleanField(default=True)

    def is_available(self, start, end, indirect=False):
        if not self.rentable:
            return False, set()
        colliding_reservations = self.reservation_set.filter(
            (Q(start_date__gte=start) & Q(end_date__lt=end)) |
            (Q(end_date__gt=start) & Q(end_date__lte=end)) |
            (Q(start_date__lte=start) & Q(end_date__gte=end))
        )
        colliding_checkouts = self.reservationcheckoutinstance_set.filter(
            (Q(reservation__start_date__gte=start) & Q(reservation__end_date__lt=end)) |
            (Q(reservation__end_date__gt=start) & Q(reservation__end_date__lte=end)) |
            (Q(reservation__start_date__lte=start) & Q(reservation__end_date__gte=end))
        )
        checkout_collisions = set()
        for reservation_relation in colliding_checkouts:
            checkout_collisions.add(reservation_relation.reservation)
        if colliding_reservations.count()+colliding_checkouts.count() > 0:
            return False, set(colliding_reservations).union(checkout_collisions)
        if indirect:
            device_available_count, device_collisions = self.device.available_count(start, end)
            if device_available_count == 0:
                return False, device_collisions
        return True, set()

    def add_to_reservation(self, reservation):
        is_available, collisions = self.is_available(reservation.start_date, reservation.end_date, indirect=True)
        if is_available:
            ReservationInstanceMembership.objects.create(reservation=reservation, instance=self)
        else:
            raise ReservationError('Dieses Gerät ist zur ausgewählten Zeit nicht verfügbar.', collisions)


class Address(models.Model):
    street = models.CharField('Straße', max_length=200, default=None, null=True)
    number = models.CharField('Hausnummer', max_length=5, default=None, null=True)
    mailbox = models.CharField('Postfach', max_length=20, default=None, null=True)
    city = models.CharField('Stadt', max_length=200)
    zip_code = models.CharField('Postleitzahl', max_length=5)

    def __str__(self):
        result = ''
        if self.mailbox is not None:
            result += 'Postfach {}\n'.format(self.mailbox)
        else:
            result += '{} {}\n'.format(self.street, self.number)
        result += '{} {}\n'.format(self.zip_code, self.city)
        return result


class Customer(models.Model):

    class Meta:
        permissions = (('view_customer', 'Can view customer'),)

    company = models.CharField('Firma', max_length=200, default=None, null=True)
    title = models.CharField('Titel', max_length=50, default=None, null=True)
    first_name = models.CharField('Vorname', max_length=200)
    last_name = models.CharField('Nachname', max_length=200)
    mail = models.EmailField('E-Mail Adresse')
    phone = models.CharField('Telefon', max_length=30, default=None, null=True)
    mobile = models.CharField('Mobiltelefon', max_length=30, default=None, null=True)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, related_name='address')
    mailing_address = models.OneToOneField(Address, on_delete=models.CASCADE, related_name='mailing_address')
    related_user = models.OneToOneField(User, on_delete=models.SET_DEFAULT, default=None, null=True)

    def __str__(self):
        string_representation = ''
        if self.title is not None:
            string_representation += self.title+' '
        string_representation += self.first_name+' '+self.last_name
        return string_representation


class Project(models.Model):
    pass


class Reservation(models.Model):

    class Meta:
        permissions = (('view_reservation', 'Can view reservation'),)

    name = models.CharField('Name', max_length=250)
    owners = models.ManyToManyField(auth_models.User, verbose_name='Besitzer')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name='Kunde')
    start_date = models.DateTimeField('Start')
    end_date = models.DateTimeField('Ende')
    description = models.TextField('Beschreibung')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, default=None)
    devices = models.ManyToManyField(Device, through='ReservationDeviceMembership')
    instances = models.ManyToManyField(Instance, through='ReservationInstanceMembership')
    checked_out_instances = models.ManyToManyField(Instance, through='ReservationCheckoutInstance',
                                                   related_name='checked_out_reservations')
    checked_in_instances = models.ManyToManyField(Instance, through='ReservationClearedInstance',
                                                  related_name='checked_in_reservations')

    @property
    def full_id(self):
        return COMPANY_SHORT+'-'+str(self.id)

    @property
    def device_count(self):
        count = 0
        count += self.instances.count()
        for device_relation in self.reservationdevicemembership_set.all():
            count += device_relation.amount
        return count

    def has_started(self):
        return timezone.now() > self.start_date

    def has_ended(self):
        return timezone.now() > self.end_date

    def checkout_instance(self, instance):
        is_available, collisions = instance.is_available(self.start_date, self.end_date)
        if is_available or self in collisions:
            try:
                instance_relation = self.reservationinstancemembership_set.get(instance=instance)
                instance_relation.delete()
            except ReservationInstanceMembership.DoesNotExist:
                try:
                    device_relation = self.reservationdevicemembership_set.get(device=instance.device)
                    if device_relation.amount > 1:
                        device_relation.amount -= 1
                        device_relation.save()
                    else:
                        device_relation.delete()
                except ReservationDeviceMembership.DoesNotExist:
                    is_available, collisions = instance.is_available(self.start_date, self.end_date, indirect=True)
                    if not is_available:
                        raise CheckoutError('Das ausgewählte Gerät ist zum gewünschten Zeitpunkt nicht verfügbar',
                                            collisions)
            ReservationCheckoutInstance.objects.create(reservation=self,
                                                       instance=instance,
                                                       checkout_date=timezone.now())
        else:
            raise CheckoutError('Das ausgewählte Gerät ist zum gewünschten Zeitpunkt nicht verfügbar.', collisions)

    def checkin_instance(self, instance):
        try:
            checked_out_relation = ReservationCheckoutInstance.objects.get(reservation=self, instance=instance)
            ReservationClearedInstance.objects.create(reservation=self,
                                                      instance=instance,
                                                      checkout_date=checked_out_relation.checkout_date,
                                                      checkin_date=timezone.now())
            checked_out_relation.delete()
        except ReservationCheckoutInstance.DoesNotExist:
            raise CheckinError('Das ausgewählte Gerät wurde nicht für diese Reservierung ausgeliehen.')

    def non_ticket_instances(self):
        latest_pdf = self.checkoutticket_set.order_by('-creation_date').first()
        if latest_pdf is not None:
            new_checkouts = self.reservationcheckoutinstance_set \
                .filter(checkout_date__gte=latest_pdf.creation_date).count()
            new_checkouts += self.abstract_items.filter(checkout_date__gte=latest_pdf.creation_date).count()
            if new_checkouts == 0:
                return False
        return True

    def checked_out_count(self):
        count = self.checked_out_instances.count()
        for item in self.abstract_items.all():
            count += item.amount
        return count

    def __str__(self):
        return '{} {} ({} - {})'.format(self.full_id, self.name, str(self.start_date), str(self.end_date))


class ReservationDeviceMembership(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.PROTECT)
    amount = models.IntegerField()


class ReservationInstanceMembership(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    instance = models.ForeignKey(Instance, on_delete=models.PROTECT)


class ReservationCheckoutInstance(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT)
    instance = models.ForeignKey(Instance, on_delete=models.PROTECT)
    checkout_date = models.DateTimeField()


class ReservationClearedInstance(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT)
    instance = models.ForeignKey(Instance, on_delete=models.PROTECT)
    checkout_date = models.DateTimeField()
    checkin_date = models.DateTimeField()


class CheckoutTicket(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=500)
    creation_date = models.DateTimeField(default=timezone.now)

    @property
    def filename(self):
        return os.path.basename(self.file_path)


class AbstractItem(models.Model):
    name = models.CharField('Name', max_length=500)
    amount = models.IntegerField('Anzahl')
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT, related_name='abstract_items')
    checkout_date = models.DateTimeField(default=timezone.now)
