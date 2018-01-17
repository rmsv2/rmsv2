from django.db import models

# Create your models here.


class Device(models.Model):
    name = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    description = models.TextField()
    price_new = models.FloatField()
    price_rental = models.FloatField()
    tags = models.ManyToManyField(Tag)


class Instance(models.Model):
    serial_number = models.CharField(max_length=200)
    inventory_number = models.CharField(max_length=200)
    identificial_description = models.TextField()
    broken = models.BooleanField()
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)


class Tag(models.Model):
    name = models.CharField(max_length=200)
    tags = models.ManyToManyField('Tag')
