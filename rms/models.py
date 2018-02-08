from django.db import models
from django.contrib.auth import models as auth_models
import string
import random
import os
from rmsv2.settings import BASE_DIR

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
    name = models.CharField('Name', max_length=200)
    top_category = models.ForeignKey('Category', on_delete=models.PROTECT, null=True, blank=True, verbose_name='Übergeordnete Kategorie')

    def __str__(self):
        return self.name

    def sub_categories_sorted_by_name(self):
        return Category.objects.filter(top_category=self).order_by('name')


class Device(models.Model):
    name = models.CharField('Name', max_length=100)
    picture = models.ImageField('Bild', upload_to=get_device_image_upload_path, blank=True, null=True, default=None)
    model_number = models.CharField('Modell Nummer', max_length=100)
    vendor = models.CharField('Hersteller', max_length=300, default='')
    description = models.TextField('Beschreibung', null=True, blank=True)
    price_new = models.FloatField('Neupreis')
    price_rental = models.FloatField('Vermietpreis')
    tags = models.ManyToManyField(Tag, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, verbose_name='Kategorie', blank=True)

    @classmethod
    def uncategorized(cls):
        return cls.objects.filter(category=None)

    def __str__(self):
        return '{} ({})'.format(self.name, self.vendor)


class Instance(models.Model):
    serial_number = models.CharField('Seriennummer', max_length=200)
    inventory_number = models.CharField('Inventarnummer', max_length=200)
    identificial_description = models.TextField('Identifikations- beschreibung', null=True, blank=True)
    broken = models.BooleanField('Defekt?')
    device = models.ForeignKey(Device, on_delete=models.PROTECT, verbose_name='Gerätetyp')
    tags = models.ManyToManyField(Tag, blank=True)
