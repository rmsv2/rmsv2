from django.forms import ModelForm, fields
from rms import models
from .form_widgets import TagInputWidget


class DeviceForm(ModelForm):

    class Meta:
        model = models.Device
        exclude = []
        widgets = {
            'tags': TagInputWidget(),
        }

    def __init__(self, *args, **kwargs):
        super(DeviceForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})


class InstanceForm(ModelForm):

    class Meta:
        model = models.Instance
        exclude = []
        widgets = {
            'tags': TagInputWidget(),
        }

    def __init__(self, *args, **kwargs):
        super(InstanceForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            if not isinstance(self.fields[fieldname], fields.BooleanField):
                self.fields[fieldname].widget.attrs.update({'class': 'form-control'})

    def disable_device_field(self):
        self.fields['device'].widget.attrs.update({'disabled': 'disabled'})


class CategoryForm(ModelForm):

    class Meta:
        model = models.Category
        exclude = []

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})
