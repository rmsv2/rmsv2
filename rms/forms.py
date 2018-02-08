from django.forms import ModelForm, fields, ValidationError
from django.contrib.auth import models as auth_models
from django.contrib.auth import forms as auth_forms
from rms import models
from .form_widgets import TagInputWidget


class BootstrapForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            if not isinstance(self.fields[fieldname], fields.BooleanField):
                self.fields[fieldname].widget.attrs.update({'class': 'form-control'})


class DeviceForm(BootstrapForm):

    class Meta:
        model = models.Device
        exclude = []
        widgets = {
            'tags': TagInputWidget(),
        }


class InstanceForm(BootstrapForm):

    class Meta:
        model = models.Instance
        exclude = []
        widgets = {
            'tags': TagInputWidget(),
        }

    def disable_device_field(self):
        self.fields['device'].widget.attrs.update({'disabled': 'disabled'})


class CategoryForm(BootstrapForm):

    class Meta:
        model = models.Category
        exclude = []

    def clean_top_category(self):
        new_top_category = self.cleaned_data['top_category']
        while new_top_category is not None:
            if new_top_category.id == self.instance.id:
                raise ValidationError('Category loop not allowed', 'category_loop')
            new_top_category = new_top_category.top_category
        return self.cleaned_data['top_category']


class ProfileChangeForm(BootstrapForm):

    class Meta:
        model = auth_models.User
        fields = ['first_name', 'last_name', 'email']


class PasswordChangeForm(auth_forms.PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            if not isinstance(self.fields[fieldname], fields.BooleanField):
                self.fields[fieldname].widget.attrs.update({'class': 'form-control'})


class CreateUserForm(auth_forms.UserCreationForm):

    class Meta:
        model = auth_models.User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_superuser']
        field_classes = {
            'username': auth_forms.UsernameField
        }

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            if not isinstance(self.fields[fieldname], fields.BooleanField):
                self.fields[fieldname].widget.attrs.update({'class': 'form-control'})


class EditUserForm(BootstrapForm):

    class Meta:
        model = auth_models.User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_superuser']


class GroupForm(BootstrapForm):

    class Meta:
        model = auth_models.Group
        fields = ['name']
