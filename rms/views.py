from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import PasswordResetForm
from django.db.models.deletion import ProtectedError
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
        path_urls.append(reverse('uncategorized_devices'))

    return path, path_urls


@login_required()
def home_view(request):
    return render(request, 'home.html', context={'title': 'Home'})


@login_required()
def add_device_view(request):
    if request.method == 'POST':
        form = forms.DeviceForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            return redirect('home')
    else:
        form = forms.DeviceForm()
    return render(request, 'inventory/device_form.html', context={'form': form,
                                                                  'add': True,
                                                                  'title': 'Gerätetyp erstellen'})


@login_required()
def edit_device_view(request, device_id):
    try:
        device = models.Device.objects.get(id=device_id)
        if request.method == 'POST':
            form = forms.DeviceForm(request.POST, instance=device)
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
def uncategorized_devices_view(request):
    return render(request, 'inventory/uncategorized_devices.html', context={'devices': models.Device.uncategorized(),
                                                                            'title': 'Unkategorisierte Geräte'})


@login_required()
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

        return render(request, 'inventory/device.html', context=context)
    except models.Device.DoesNotExist:
        return HttpResponse('', status=404)


@login_required()
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
def groups_list_view(request):
    groups = Group.objects.all()
    return render(request, 'settings/groups.html', context={'title': 'Gruppen',
                                                            'path': [{'text': 'Gruppen'}],
                                                            'groups': groups})


@login_required()
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
def remove_group_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
        group.delete()
    except Group.DoesNotExist:
        pass
    return redirect('groups_list')


@login_required()
def group_view(request, group_id):
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
