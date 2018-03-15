from django.db import models
from django.contrib.auth import models as auth_models
from djmoney.models.fields import MoneyField
import string
import random
import os
from rmsv2.settings import BASE_DIR, COMPANY_SHORT

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

    @classmethod
    def uncategorized(cls):
        return cls.objects.filter(category=None)

    def __str__(self):
        return '{} ({})'.format(self.name, self.vendor)


class Instance(models.Model):

    class Meta:
        permissions = (('view_unrentable', 'Can view unrentable inventory'),
                       ('view_instance', 'Can view instance'),)

    serial_number = models.CharField('Seriennummer', max_length=200)
    inventory_number = models.CharField('Inventarnummer', max_length=200)
    identificial_description = models.TextField('Identifikations- beschreibung', null=True, blank=True)
    broken = models.BooleanField('Defekt?')
    rentable = models.BooleanField('Ausleihbar', default=False)
    device = models.ForeignKey(Device, on_delete=models.PROTECT, verbose_name='Gerätetyp')
    tags = models.ManyToManyField(Tag, blank=True)


class Address(models.Model):
    street = models.CharField('Straße', max_length=200, default=None, null=True)
    number = models.CharField('Hausnummer', max_length=5, default=None, null=True)
    mailbox = models.CharField('Postfach', max_length=20, default=None, null=True)
    city = models.CharField('Stadt', max_length=200)
    zip_code = models.CharField('Postleitzahl', max_length=5)


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
        permissions = (('view_all_reservations', 'Can view all reservations'),)

    name = models.CharField('Name', max_length=250)
    owners = models.ManyToManyField(auth_models.User, verbose_name='Besitzer')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name='Kunde')
    start_date = models.DateTimeField('Start')
    end_date = models.DateTimeField('Ende')
    description = models.TextField('Beschreibung')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, default=None)
    devices = models.ManyToManyField(Device, through='ReservationDeviceMembership')
    instances = models.ManyToManyField(Instance)

    @property
    def full_id(self):
        return COMPANY_SHORT+'-'+str(self.id)


class ReservationDeviceMembership(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.PROTECT)
    amount = models.IntegerField()
