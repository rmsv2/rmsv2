from django.forms import ModelForm, fields, ValidationError
from django import forms
from django.contrib.auth import models as auth_models
from django.contrib.auth import forms as auth_forms
from rms import models
from .form_widgets import TagInputWidget


class BootstrapForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            if not isinstance(self.fields[fieldname], fields.BooleanField)\
                    and not isinstance(self.fields[fieldname], fields.ImageField):
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


class AddressForm(BootstrapForm):

    class Meta:
        model = models.Address
        fields = ['street', 'number', 'mailbox', 'city', 'zip_code']

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.fields['street'].required = False
        self.fields['number'].required = False
        self.fields['mailbox'].required = False

    def clean(self):
        cleaned_data = super(AddressForm, self).clean()
        street = cleaned_data.get('street')
        number = cleaned_data.get('number')
        mailbox = cleaned_data.get('mailbox')

        if street and not number and not mailbox:
            raise ValidationError('Es wird eine Hausnummer benötigt.')
        if not street and number and not mailbox:
            raise ValidationError('Es wird eine Straße benötigt.')
        if not street and not number and not mailbox:
            raise ValidationError('Es wird entwerder eine Anschrift oder ein Postfach benötigt.')
        if street or number:
            if mailbox:
                raise ValidationError('Bitte nur eine Anschrift oder ein Postfach angeben.')
        return cleaned_data


class CustomerForm(BootstrapForm):

    class Meta:
        model = models.Customer
        exclude = ['mailing_address', 'address', 'related_user']

    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.fields['company'].required = False
        self.fields['title'].required = False
        self.fields['phone'].required = False
        self.fields['mobile'].required = False

    def clean(self):
        cleaned_data = super(CustomerForm, self).clean()
        phone = cleaned_data.get('phone')
        mobile = cleaned_data.get('mobile')

        if not phone and not mobile:
            raise ValidationError('Telefon- oder Mobilnummer wird benötigt.')

        return cleaned_data


class GroupForm(BootstrapForm):

    class Meta:
        model = auth_models.Group
        fields = ['name']


class ReservationForm(BootstrapForm):

    class Meta:
        model = models.Reservation
        fields = ['name', 'description', 'customer', 'start_date', 'end_date', 'owners']

    def __init__(self, *args, **kwargs):
        super(ReservationForm, self).__init__(*args, **kwargs)
        self.fields['description'].required = False

    def clean_start_date(self):
        new_start_date = self.cleaned_data.get('start_date')
        old_start_date = self.instance.start_date
        if old_start_date is not None:
            if new_start_date < old_start_date:
                for device_relation in self.instance.reservationdevicemembership_set.all():
                    if device_relation.amount > device_relation.device.available_count(new_start_date, old_start_date):
                        raise ValidationError('Starttermin kann nicht geändert werden, da nicht alle reservierten '
                                              'Geräte verfügbar sind')
                for instance in self.instance.instances.all():
                    if not instance.is_available(new_start_date, old_start_date):
                        raise ValidationError('Starttermin kann nicht geändert werden, da nicht alle reservierten '
                                              'Geräte verfügbar sind')
        return new_start_date

    def clean_end_date(self):
        new_end_date = self.cleaned_data.get('end_date')
        old_end_date = self.instance.end_date
        if old_end_date is not None:
            if new_end_date > old_end_date:
                available_error = False
                collisions = set()
                for device_relation in self.instance.reservationdevicemembership_set.all():
                    available_count, collision = device_relation.device.available_count(old_end_date, new_end_date)
                    if device_relation.amount > available_count:
                        available_error = True
                        collisions = collisions.union(collision)
                for instance in self.instance.instances.all():
                    is_available, collision = instance.is_available(old_end_date, new_end_date)
                    if not is_available:
                        available_error = True
                        collisions = collisions.union(collision)
                if available_error:
                    errors = []
                    for reservation in collisions:
                        errors.append(ValidationError('Kollision mit: {} {}'.format(reservation.full_id,
                                                                                    reservation.name)))
                    raise ValidationError(errors)
        return new_end_date

