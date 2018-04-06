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

    def clean(self):
        cleaned_data = super(ReservationForm, self).clean()
        old_start_date = self.instance.start_date
        old_end_date = self.instance.end_date
        new_start_date = cleaned_data.get('start_date')
        new_end_date = cleaned_data.get('end_date')

        if new_start_date >= new_end_date:
            raise ValidationError({'end_date': ValidationError('Das Ende muss nach dem Start liegen.')})

        if old_end_date is None or old_start_date is None:
            return cleaned_data

        def all_available(start, end, error_target=None):
            available_error = False
            collisions = set()
            for device_relation in self.instance.reservationdevicemembership_set.all():
                available_count, collision = device_relation.device.available_count(start, end)
                if device_relation.amount > available_count:
                    available_error = True
                    collisions = collisions.union(collision)
            for instance in self.instance.instances.all():
                is_available, collision = instance.is_available(start, end)
                if not is_available:
                    available_error = True
                    collisions = collisions.union(collision)
            for instance in self.instance.checked_out_instances.all():
                is_available, collision = instance.is_available(start, end)
                if not is_available:
                    available_error = True
                    collisions = collisions.union(collision)
            if available_error:
                errors = []
                for reservation in collisions:
                    errors.append(ValidationError('Kollision mit: {} {}'.format(reservation.full_id,
                                                                                reservation.name)))
                if error_target is not None:
                    raise ValidationError({error_target: errors})
                else:
                    raise ValidationError(errors)
        validation_errors = []
        if new_start_date >= old_end_date or new_end_date <= old_start_date:
            if self.instance.checked_out_instances.count() > 0:
                raise ValidationError('Wenn schon ein Gerät ausgeliehen ist '
                                      'kann die Reservierung nicht komplett verschoben werden.')
            all_available(new_start_date, new_end_date)
        else:
            try:
                if new_start_date < old_start_date:
                    all_available(new_start_date, old_start_date, 'start_date')
            except ValidationError as error:
                validation_errors.append(error)

            try:
                if new_end_date > old_end_date:
                    all_available(old_end_date, new_end_date, 'end_date')
            except ValidationError as error:
                validation_errors.append(error)

            if len(validation_errors) > 0:
                raise ValidationError(validation_errors)

        return cleaned_data


class AbstractItemForm(BootstrapForm):

    class Meta:
        model = models.AbstractItem
        exclude = ['reservation', 'checkout_date']

    def clean_amount(self):
        amount = self.cleaned_data['amount']

        if amount < 1:
            raise ValidationError('Es ist mindestens der Wert 1 nötig.')
        else:
            return amount
