from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import PasswordResetForm
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from rms import forms
from . import models
from .decorators import permission_required

# Create your views here.


def redirect_previous(request):
    if 'redirect' in request.GET:
        return redirect(request.GET['redirect'])
    elif 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect('home')


def get_path(category):
    path = []
    path_urls = []
    actual_category = category
    while actual_category is not None:
        path.append({'text': actual_category.name,
                     'url': reverse('category', kwargs={'category_id': actual_category.id})})
        path_urls.append(reverse('category', kwargs={'category_id': actual_category.id}))
        actual_category = actual_category.top_category
    path.reverse()

    if len(path_urls) is 0:
        path_urls.append(reverse('uncategorized'))
        path.append({'text': 'Unkategorisiert',
                     'url': reverse('uncategorized')})

    return path, path_urls


@login_required()
def home_view(request):
    return render(request, 'home.html', context={'title': 'Home'})


@login_required()
@permission_required('rms.add_device')
def add_device_view(request):
    if request.method == 'POST':
        form = forms.DeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=True)
            return redirect('device', device_id=device.id)
    else:
        form = forms.DeviceForm()
    return render(request, 'inventory/device_form.html', context={'form': form,
                                                                  'add': True,
                                                                  'title': 'Gerätetyp erstellen'})


@login_required()
@permission_required('rms.change_device')
def edit_device_view(request, device_id):
    try:
        device = models.Device.objects.get(id=device_id)
        if request.method == 'POST':
            form = forms.DeviceForm(request.POST, files=request.FILES, instance=device)
            if form.is_valid():
                form.save()
                return redirect('device', device_id=device.id)
        else:
            form = forms.DeviceForm(instance=device)

        return render(request, 'generics/form.html', context={'title': 'Grätetyp bearbeiten',
                                                              'form': form})
    except models.Device.DoesNotExist:
        return HttpResponse('', status=404)


@login_required()
@permission_required('rms.delete_device')
def delete_device_view(request, device_id):
    try:
        device = models.Device.objects.get(id=device_id)

        try:
            device.delete()
        except ProtectedError:
            return redirect(reverse('device', kwargs={'device_id': device.id})+'?protected_error=1')

    except models.Device.DoesNotExist:
        pass

    return redirect_previous(request)


@login_required()
@permission_required('rms.view_device')
def device_view(request, device_id):
    try:
        device = models.Device.objects.get(id=device_id)

        path, path_urls = get_path(device.category)

        context = {'title': device.name,
                   'device': device,
                   'path': path,
                   'category_path_urls': path_urls}
        if 'protected_error' in request.GET and request.GET['protected_error'] == '1':
            context['protected_error'] = True

        if request.user.has_perm('rms.view_unrentable'):
            context['instances'] = device.instance_set.all()
        else:
            context['instances'] = device.instance_set.filter(rentable=True)

        return render(request, 'inventory/device_instances.html', context=context)
    except models.Device.DoesNotExist:
        return HttpResponse('', status=404)


@login_required()
@permission_required('rms.view_device')
def device_reservations_view(request, device_id):
    try:
        device = models.Device.objects.get(id=device_id)

        path, path_urls = get_path(device.category)

        context = {'title': device.name,
                   'device': device,
                   'path': path,
                   'category_path_urls': path_urls}
        if 'protected_error' in request.GET and request.GET['protected_error'] == '1':
            context['protected_error'] = True

        if request.user.has_perm('rms.view_unrentable'):
            context['instances'] = device.instance_set.all()
        else:
            context['instances'] = device.instance_set.filter(rentable=True)

        return render(request, 'inventory/device_reservation.html', context=context)
    except models.Device.DoesNotExist:
        return HttpResponse('', status=404)


@login_required()
@permission_required('rms.view_device')
def device_instance_view(request, device_id, instance_id):
    try:
        device = models.Device.objects.get(id=device_id)

        path, path_urls = get_path(device.category)

        context = {'title': device.name,
                   'device': device,
                   'path': path,
                   'category_path_urls': path_urls}
        if 'protected_error' in request.GET and request.GET['protected_error'] == '1':
            context['protected_error'] = True

        if request.user.has_perm('rms.view_unrentable'):
            context['instances'] = device.instance_set.all()
        else:
            context['instances'] = device.instance_set.filter(rentable=True)

        try:
            instance = models.Instance.objects.get(id=instance_id)
            context['instance'] = instance
            return render(request, 'inventory/device_instance.html', context=context)
        except models.Instance.DoesNotExist:
            return redirect('device', device_id=device.id)
    except models.Device.DoesNotExist:
        return HttpResponse('', status=404)


@login_required()
@permission_required('rms.add_instance')
def create_instance_view(request, device_id):
    try:
        device = models.Device.objects.get(id=device_id)
        if request.method == 'POST':
            post = request.POST.dict()
            post['device'] = '{}'.format(device.id)
            form = forms.InstanceForm(post)
            if form.is_valid():
                form.save()
                return redirect('device', device_id=device.id)
        else:
            form = forms.InstanceForm(initial={'device': device})
        form.disable_device_field()
        path, path_urls = get_path(device.category)
        path.insert(0, {'text': '<i class="fa fa-cubes"></i>Inventar'})
        path.append({'url': reverse('device', kwargs={'device_id': device.id}), 'text': device.name})
        return render(request, 'generics/form.html', context={'title': 'Instanz erstellen',
                                                              'form': form,
                                                              'path': path,
                                                              'category_path_urls': path_urls})
    except models.Device.DoesNotExist:
        return HttpResponse('', status=404)


@login_required()
@permission_required('rms.change_instance')
def edit_instance_view(request, device_id, instance_id):
    try:
        device = models.Device.objects.get(id=device_id)
        instance = models.Instance.objects.get(id=instance_id)

        if request.method == 'POST':
            post = request.POST.dict()
            post['device'] = '{}'.format(device.id)
            form = forms.InstanceForm(post, instance=instance)
            if form.is_valid():
                form.save()
                return redirect('device', device_id=device.id)
        else:
            form = forms.InstanceForm(instance=instance)
        form.disable_device_field()
        path, path_urls = get_path(device.category)
        path.insert(0, {'text': '<i class="fa fa-cubes"></i>Inventar'})
        path.append({'url': reverse('device', kwargs={'device_id': device.id}), 'text': device.name})
        return render(request, 'generics/form.html', context={'title': 'Instanz erstellen',
                                                              'form': form,
                                                              'path': path,
                                                              'category_path_urls': path_urls})

    except models.Device.DoesNotExist:
        return HttpResponse('', status=404)
    except models.Instance.DoesNotExist:
        return redirect('device', device_id)


@login_required()
@permission_required('rms.delete_instance')
def delete_instance_view(request, device_id, instance_id):
    try:
        device = models.Device.objects.get(id=device_id)
        instance = models.Instance.objects.get(id=instance_id)

        if request.method == 'POST':
            instance.delete()
            return redirect('device', device_id=device.id)
    except models.Device.DoesNotExist:
        return HttpResponse('', status=404)
    except models.Instance.DoesNotExist:
        return redirect('device', device_id=device_id)


@login_required()
@permission_required('rms.add_category')
def create_category_view(request, category_id=None):
    if request.method == 'POST':
        form = forms.CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            return redirect('category', category_id=category.id)
    else:
        try:
            category = models.Category.objects.get(id=category_id)
            form = forms.CategoryForm(category=category)
        except models.Category.DoesNotExist:
            form = forms.CategoryForm()
    return render(request, 'generics/form.html', context={'title': 'Kategorie erstellen',
                                                          'form': form})


@login_required()
@permission_required('rms.view_category')
def category_view(request, category_id):
    try:
        category = models.Category.objects.get(id=category_id)

        path = []
        path_urls = []
        actual_category = category
        while actual_category is not None:
            path.append({'text': actual_category.name,
                         'url': reverse('category', kwargs={'category_id': actual_category.id})})
            path_urls.append(reverse('category', kwargs={'category_id': actual_category.id}))
            actual_category = actual_category.top_category
        path.reverse()

        context = {'title': 'Kategorie: {}'.format(category.name),
                   'path': path,
                   'category_path_urls': path_urls,
                   'category': category}

        if 'protected_error' in request.GET and request.GET['protected_error'] == '1':
            context['protected_error'] = True

        return render(request, 'inventory/category.html', context=context)

    except models.Category.DoesNotExist:
        return redirect('home')


@login_required()
@permission_required('rms.view_category')
def uncategorized_view(request):
    return render(request, 'inventory/uncategorized.html', context={'devices': models.Device.uncategorized(),
                                                                            'title': 'Unkategorisierte Geräte'})


@login_required()
@permission_required('rms.change_category')
def edit_category_view(request, category_id):
    try:
        category = models.Category.objects.get(id=category_id)
        if request.method == 'POST':
            form = forms.CategoryForm(request.POST, instance=category)
            if form.is_valid():
                form.save()
                return redirect('category', category_id=category.id)
        else:
            form = forms.CategoryForm(instance=category)
        path, path_urls = get_path(category)
        path.insert(0, {'text': '<i class="fa fa-cubes"></i> Inventar'})
        return render(request, 'generics/form.html', context={'title': 'Kategorie bearbeiten',
                                                              'form': form,
                                                              'path': path,
                                                              'category_path_urls': path_urls})
    except models.Category.DoesNotExist:
        return redirect('home')


@login_required()
@permission_required('rms.delete_category')
def remove_category_view(request, category_id):
    try:
        category = models.Category.objects.get(id=category_id)
        if request.method == 'POST':
            top_category = category.top_category
            try:
                category.delete()
            except ProtectedError:
                return redirect(reverse('category', kwargs={'category_id': category.id})+'?protected_error=1')

            if top_category is not None:
                return redirect('category', category_id=top_category.id)
        else:
            return redirect('category', category_id=category.id)
    except models.Category.DoesNotExist:
        pass
    return redirect('home')


@login_required()
def profile_view(request):
    return render(request, 'settings/profile.html', context={'title': 'Profil',
                                                             'path': [{'text': 'Profil'}]})


@login_required()
def edit_profile_view(request):
    if request.method == 'POST':
        form = forms.ProfileChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = forms.ProfileChangeForm(instance=request.user)
    return render(request, 'settings/settings_form.html', context={'title': 'Profil bearbeiten',
                                                                  'path': [{'text': 'Profil'}],
                                                                  'form': form})


@login_required()
def change_password_view(request):
    if request.method == 'POST':
        form = forms.PasswordChangeForm(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = forms.PasswordChangeForm(user=request.user)
    return render(request, 'settings/settings_form.html', context={'title': 'Passwort ändern',
                                                                   'path': [{'text': 'Profil'}],
                                                                   'form': form})


@login_required()
@permission_required('auth.view_user')
def users_list_view(request):
    users = User.objects.all()
    return render(request, 'settings/users.html', context={'title': 'Benutzer',
                                                           'path': [{'text': 'Benutzer'}],
                                                           'users': users})


@login_required()
@permission_required('auth.view_user')
def user_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return render(request, 'settings/user.html', context={'title': user.username,
                                                              'path': [{'text': 'Benutzer',
                                                                        'url': reverse('users_list')},
                                                                       {'text': user.username}],
                                                              'user': user})
    except User.DoesNotExist:
        return redirect('users_list')


@login_required()
@permission_required('auth.delete_user')
def delete_user_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
    except User.DoesNotExist:
        pass
    return redirect('users_list')


@login_required()
@permission_required('auth.change_user')
def user_edit_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        if request.method == 'POST':
            form = forms.EditUserForm(data=request.POST, instance=user)
            if form.is_valid():
                form.save()
                return redirect('user', user_id=user.id)
        else:
            form = forms.EditUserForm(instance=user)
        return render(request, 'settings/settings_form.html', context={'title': user.username,
                                                                       'path': [{'text': 'Benutzer',
                                                                                 'url': reverse('users_list')},
                                                                                {'text': user.username,
                                                                                 'url': reverse('user',
                                                                                                kwargs={
                                                                                                    'user_id': user.id
                                                                                                })}],
                                                                       'form': form})
    except User.DoesNotExist:
        return redirect('users_list')


@login_required()
@permission_required('auth.add_user')
def create_user_view(request):
    if request.method == 'POST':
        form = forms.CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users_list')
    else:
        form = forms.CreateUserForm()
    return render(request, 'settings/settings_form.html', context={'title': 'Benutzer erstellen',
                                                                   'path': [{'text': 'Benutzer',
                                                                             'url': reverse('users_list')}],
                                                                   'form': form})


@login_required()
@permission_required('auth.change_user')
def user_password_reset(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        if request.method == 'POST':
            form = PasswordResetForm(data={'email': user.email})
            form.is_valid()
            form.save(request=request)
            return render(request, 'settings/password_reseted.html', context={'title': 'Password zurückgesetzt',
                                                                              'path': [{'text': 'Benutzer',
                                                                                        'url': reverse('users_list')},
                                                                                       {'text': user.username,
                                                                                        'url': reverse('user',
                                                                                                       kwargs={
                                                                                                           'user_id':
                                                                                                               user.id
                                                                                                       })}],
                                                                              'user': user})
        else:
            return redirect('user', user_id=user.id)
    except User.DoesNotExist:
        return redirect('users_list')


@login_required()
@permission_required('auth.view_group')
def groups_list_view(request):
    groups = Group.objects.all()
    return render(request, 'settings/groups.html', context={'title': 'Gruppen',
                                                            'path': [{'text': 'Gruppen'}],
                                                            'groups': groups})


@login_required()
@permission_required('auth.add_group')
def add_group_view(request):
    if request.method == 'POST':
        form = forms.GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            return redirect('group', group_id=group.id)
    else:
        form = forms.GroupForm()
    return render(request, 'settings/settings_form.html', context={'title': 'Gruppe erstellen',
                                                                   'path': [{'text': 'Gruppen',
                                                                             'url': reverse('groups_list')},
                                                                            {'text': 'Gruppe erstellen'}],
                                                                   'form': form})


@login_required()
@permission_required('auth.change_group')
def edit_group_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
        if request.method == 'POST':
            form = forms.GroupForm(data=request.POST, instance=group)
            if form.is_valid():
                form.save()
                return redirect('group', group_id=group.id)
        else:
            form = forms.GroupForm(instance=group)
        return render(request, 'settings/settings_form.html', context={'title': 'Gruppe bearbeiten',
                                                                       'path': [{'text': 'Gruppen',
                                                                                 'url': reverse('groups_list')},
                                                                                {'text': group.name,
                                                                                 'url': reverse('group', kwargs={
                                                                                     'group_id': group.id
                                                                                 })}],
                                                                       'form': form})
    except Group.DoesNotExist:
        return redirect('groups_list')


@login_required()
@permission_required('auth.delete_group')
def remove_group_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
        group.delete()
    except Group.DoesNotExist:
        pass
    return redirect('groups_list')


@login_required()
@permission_required('auth.change_group')
def modify_group_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
        if request.method == 'POST':
            if 'permission' in request.POST:
                try:
                    perm = Permission.objects.get(id=request.POST['permission'])
                    group.permissions.add(perm)
                except Permission.DoesNotExist:
                    pass
            if 'user' in request.POST:
                try:
                    user = User.objects.get(id=request.POST['user'])
                    group.user_set.add(user)
                except User.DoesNotExist:
                    pass
            if 'delete_permission' in request.POST:
                try:
                    perm = Permission.objects.get(id=request.POST['delete_permission'])
                    group.permissions.remove(perm)
                except Permission.DoesNotExist:
                    pass
            if 'delete_user' in request.POST:
                try:
                    user = User.objects.get(id=request.POST['delete_user'])
                    group.user_set.remove(user)
                except User.DoesNotExist:
                    pass
        return redirect('group', group_id=group_id)
    except Group.DoesNotExist:
        return redirect('groups_list')


@login_required()
@permission_required('auth.view_group')
def group_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
        available_permissions = list(set(group.permissions.model.objects.all()) ^ set(group.permissions.all()))
        available_users = list(set(group.user_set.model.objects.all()) ^ set(group.user_set.all()))
        return render(request, 'settings/group.html', context={'title': group.name,
                                                               'path': [{'text': 'Gruppen',
                                                                         'url': reverse('groups_list')},
                                                                        {'text': group.name,
                                                                         'url': reverse('group', kwargs={
                                                                             'group_id': group_id
                                                                         })}],
                                                               'group': group,
                                                               'available_permissions': available_permissions,
                                                               'available_users': available_users})
    except Group.DoesNotExist:
        return redirect('groups_list')


@login_required()
def search_view(request):
    if request.method == 'GET' and 'search' in request.GET:
        search_string = request.GET['search']
        context = {
            'search_string': search_string,
            'title': 'Suche {}'.format(search_string)
        }
        if request.user.has_perm('rms.view_device'):
            devices = models.Device.objects.filter(Q(instance__identificial_description__icontains=search_string) |
                                                   Q(instance__inventory_number__icontains=search_string) |
                                                   Q(instance__serial_number__icontains=search_string) |
                                                   Q(description__icontains=search_string) |
                                                   Q(name__icontains=search_string) |
                                                   Q(vendor__icontains=search_string) |
                                                   Q(model_number__icontains=search_string))
            context['devices'] = set(devices)

        if request.user.has_perm('rms.view_reservation'):
            reservations = models.Reservation.objects.filter(Q(name__icontains=search_string) |
                                                             Q(description__icontains=search_string))
            context['reservations'] = set(reservations)

        if request.user.has_perm('rms.view_customer'):
            customers = models.Customer.objects.filter(Q(first_name__icontains=search_string) |
                                                       Q(last_name__icontains=search_string) |
                                                       Q(mail__icontains=search_string) |
                                                       Q(phone__icontains=search_string) |
                                                       Q(mobile__icontains=search_string) |
                                                       Q(address__city__icontains=search_string) |
                                                       Q(address__street__icontains=search_string) |
                                                       Q(address__zip_code__icontains=search_string) |
                                                       Q(address__mailbox__icontains=search_string) |
                                                       Q(mailing_address__city__icontains=search_string) |
                                                       Q(mailing_address__street__icontains=search_string) |
                                                       Q(mailing_address__zip_code__icontains=search_string) |
                                                       Q(mailing_address__mailbox__icontains=search_string))
            context['customers'] = set(customers)

        return render(request, 'search.html', context=context)
    else:
        return redirect(request.path)


@login_required()
@permission_required('rms.view_customer')
def customers_view(request):
    customers = models.Customer.objects.all()

    return render(request, 'customers/customers.html', context={'title': 'Kundendaten',
                                                                'customers': customers})


@login_required()
@permission_required('rms.add_customer')
def create_customer_view(request):
    mailing_address_equals_address = False
    if request.method == 'POST':
        customer_form = forms.CustomerForm(request.POST, prefix='customer')
        address_form = forms.AddressForm(request.POST, prefix='address')
        if 'mailing_address_equals_address' in request.POST and request.POST['mailing_address_equals_address'] == 'on':
            mailing_address_equals_address = True
            mailing_address_form = forms.AddressForm(prefix='mailing_address')
        else:
            mailing_address_form = forms.AddressForm(request.POST, prefix='mailing_address')
        if mailing_address_equals_address:
            if customer_form.is_valid() and address_form.is_valid():
                customer = customer_form.save(False)
                address = address_form.save(True)
                customer.address = address
                customer.mailing_address = address
                customer.save()
                return redirect('customer', customer_id=customer.id)
        else:
            if mailing_address_form.is_valid() and customer_form.is_valid() and address_form.is_valid():
                customer = customer_form.save(False)
                address = address_form.save(True)
                mailing_address = mailing_address_form.save(True)
                customer.address = address
                customer.mailing_address = mailing_address
                customer.save()
                return redirect('customer', customer_id=customer.id)

    else:
        customer_form = forms.CustomerForm(prefix='customer')
        address_form = forms.AddressForm(prefix='address')
        mailing_address_form = forms.AddressForm(prefix='mailing_address')
    address_form.fields.pop('mailbox')
    return render(request, 'customers/customer_form.html', context={'title': 'Kunde anlegen',
                                                                    'customer_form': customer_form,
                                                                    'address_form': address_form,
                                                                    'mailing_address_form': mailing_address_form,
                                                                    'mailing_address_equals_address':
                                                                        mailing_address_equals_address})


@login_required()
@permission_required('rms.delete_customer')
def remove_customer_view(request, customer_id):
    if request.method == 'POST':
        try:
            customer = models.Customer.objects.get(id=customer_id)
            customer.delete()
        except models.Customer.DoesNotExist:
            pass

    return redirect('customers')


@login_required()
@permission_required('rms.view_customer')
def customer_view(request, customer_id):
    try:
        customer = models.Customer.objects.get(id=customer_id)
        return render(request, 'customers/customer.html', context={'title': 'Kundeninformationen',
                                                                   'customer': customer})
    except models.Customer.DoesNotExist:
        return redirect('customers')


@login_required()
@permission_required('rms.change_customer')
def edit_customer_view(request, customer_id):
    try:
        customer = models.Customer.objects.get(id=customer_id)
        mailing_address_equals_address = False
        if request.method == 'POST':
            customer_form = forms.CustomerForm(request.POST, prefix='customer', instance=customer)
            address_form = forms.AddressForm(request.POST, prefix='address', instance=customer.address)
            if 'mailing_address_equals_address' in request.POST \
                    and request.POST['mailing_address_equals_address'] == 'on':
                mailing_address_equals_address = True
                mailing_address_form = forms.AddressForm(prefix='mailing_address', instance=customer.mailing_address)
            else:
                mailing_address_form = forms.AddressForm(request.POST, prefix='mailing_address',
                                                         instance=customer.mailing_address)
            if mailing_address_equals_address:
                if customer_form.is_valid() and address_form.is_valid():
                    customer = customer_form.save(False)
                    address = address_form.save(True)
                    customer.address = address
                    customer.mailing_address = address
                    customer.save()
                    return redirect('customer', customer_id=customer.id)
            else:
                if mailing_address_form.is_valid() and customer_form.is_valid() and address_form.is_valid():
                    customer = customer_form.save(False)
                    address = address_form.save(True)
                    mailing_address = mailing_address_form.save(True)
                    customer.address = address
                    customer.mailing_address = mailing_address
                    customer.save()
                    return redirect('customer', customer_id=customer.id)

        else:
            customer_form = forms.CustomerForm(prefix='customer', instance=customer)
            address_form = forms.AddressForm(prefix='address', instance=customer.address)
            mailing_address_form = forms.AddressForm(prefix='mailing_address', instance=customer.mailing_address)
            if customer.address == customer.mailing_address:
                mailing_address_equals_address = True
        address_form.fields.pop('mailbox')
        return render(request, 'customers/customer_form.html', context={'title': 'Kunde bearbeiten',
                                                                        'customer': customer,
                                                                        'customer_form': customer_form,
                                                                        'address_form': address_form,
                                                                        'mailing_address_form': mailing_address_form,
                                                                        'mailing_address_equals_address':
                                                                            mailing_address_equals_address,
                                                                        'edit': True})
    except models.Customer.DoesNotExist:
        return redirect('customers')


@login_required()
@permission_required('rms.view_reservation')
def reservations_view(request):
    if 'all' in request.GET and request.GET['all'] == 'yes' and request.user.is_superuser:
        reservations = models.Reservation.objects.order_by('start_date').all()
        show_all = True
    else:
        reservations = request.user.reservation_set.order_by('start_date').all()
        show_all = False
    reservations_feed_url = request.build_absolute_uri(reverse('reservations_feed'))
    return render(request, 'reservation/reservations.html', context={'title': 'Reservierungen',
                                                                     'reservations': reservations,
                                                                     'show_all': show_all,
                                                                     'reservations_feed_url': reservations_feed_url})


@login_required()
@permission_required('rms.add_reservation')
def create_reservation_view(request):
    if request.method == 'POST':
        form = forms.ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save()
            reservation.owners.add(request.user)
            reservation.save()
            return redirect('reservations')
    else:
        form = forms.ReservationForm(initial={'owners': request.user})
    return render(request, 'reservation/reservation_form.html', context={'title': 'Reservierung erstellen',
                                                                         'path': [{'text': '<i class="fa fa-file-text">'
                                                                                           '</i>Reservierungen',
                                                                                  'url': reverse('reservations')},
                                                                                  {'text': 'Reservierung erstellen'}],
                                                                         'form': form})


@login_required()
@permission_required('rms.view_reservation')
def reservation_view(request, reservation_id):
    try:
        reservation = models.Reservation.objects.get(id=reservation_id)
        return render(request, 'reservation/reservation.html', context={'title': 'Reservierung',
                                                                        'reservation': reservation})
    except models.Reservation.DoesNotExist:
        return redirect('reservations')


@login_required()
@permission_required('rms.change_reservation')
def edit_reservation_view(request, reservation_id):
    try:
        reservation = models.Reservation.objects.get(id=reservation_id)
        if request.method == 'POST':
            form = forms.ReservationForm(request.POST, instance=reservation)
            if form.is_valid():
                form.save()
                return redirect('reservation', reservation_id)
        else:
            form = forms.ReservationForm(instance=reservation)
        context = {
            'title': 'Reservierung bearbeiten',
            'path': [
                {'text': '<i class="fa fa-file-text"></i>Reservierungen',
                 'url': reverse('reservations')},
                {'text': reservation.name,
                 'url': reverse('reservation', kwargs={'reservation_id': reservation_id})}
            ],
            'form': form
        }
        return render(request, 'reservation/reservation_form.html', context=context)
    except models.Reservation.DoesNotExist:
        return redirect('reservations')


@login_required()
@permission_required('rms.delete_permission')
def remove_reservation_view(request, reservation_id):
    try:
        reservation = models.Reservation.objects.get(id=reservation_id)
        if request.method == 'POST':
            reservation.delete()
    except models.Reservation.DoesNotExist:
        pass
    return redirect('reservations')


@login_required()
@permission_required('rms.change_reservation')
def remove_device_from_reservation(request, reservation_id, device_id):
    try:
        reservation = models.Reservation.objects.get(id=reservation_id)
        if request.method == 'POST':
            try:
                device = models.Device.objects.get(id=device_id)
                reservation.reservationdevicemembership_set.get(device=device).delete()
            except models.Device.DoesNotExist:
                pass
        return redirect('reservation', reservation_id=reservation_id)
    except models.Reservation.DoesNotExist:
        return redirect('reservations')


@login_required()
@permission_required('rms.change_reservation')
def remove_instance_from_reservation(request, reservation_id, instance_id):
    try:
        reservation = models.Reservation.objects.get(id=reservation_id)
        if request.method == 'POST':
            try:
                instance = models.Instance.objects.get(id=instance_id)
                reservation.reservationinstancemembership_set.get(instance=instance).delete()
            except models.Instance.DoesNotExist:
                pass
        return redirect('reservation', reservation_id=reservation.id)
    except models.Reservation.DoesNotExist:
        return redirect('reservations')
