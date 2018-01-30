from django.db import models

# Create your models here.


class Tag(models.Model):
    name = models.CharField('Name', max_length=200, unique=True, primary_key=True)
    tags = models.ManyToManyField('Tag')


class Device(models.Model):
    name = models.CharField('Name', max_length=100)
    model_number = models.CharField('Modell Nummer', max_length=100)
    vendor = models.CharField('Hersteller', max_length=300, default='')
    description = models.TextField('Beschreibung')
    price_new = models.FloatField('Neupreis')
    price_rental = models.FloatField('Vermietpreis')
    tags = models.ManyToManyField(Tag, blank=True)

    @classmethod
    def untagged(cls):
        return cls.objects.filter(tags=None)


class Instance(models.Model):
    serial_number = models.CharField('Seriennummer', max_length=200)
    inventory_number = models.CharField('Inventarnummer', max_length=200)
    identificial_description = models.TextField('Identifikationsbeschreibung')
    broken = models.BooleanField('Defekt?')
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
