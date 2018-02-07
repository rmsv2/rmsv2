from django.urls import path

from . import views
from .api_views.inventory import *

urlpatterns = [
    path('', views.home_view, name='home'),
    path('inventory/addDevice', views.add_device_view, name='add_device'),
    path('inventory/devices/uncategorized', views.uncategorized_devices_view, name='uncategorized_devices'),
    path('inventory/devices/<int:device_id>/delete', views.delete_device_view, name='delete_device'),
    path('inventory/devices/<int:device_id>/edit', views.edit_device_view, name='edit_device'),
    path('inventory/devices/<int:device_id>', views.device_view, name='device'),
    path('inventory/devices/<int:device_id>/instances/add', views.create_instance_view, name='create_instance'),
    path('inventory/devices/<int:device_id>/instances/<int:instance_id>/edit',
         views.edit_instance_view, name='edit_instance'),
    path('inventory/devices/<int:device_id>/instances/<int:instance_id>/delete',
         views.delete_instance_view, name='delete_instance'),

    path('inventory/categories/add', views.create_category_view, name='create_category'),
    path('inventory/categories/<int:category_id>', views.category_view, name='category'),
    path('inventory/categories/<int:category_id>/edit', views.edit_category_view, name='edit_category'),
    path('inventory/categories/<int:category_id>/delete', views.remove_category_view, name='delete_category'),

    path('settings/profile', views.profile_view, name='profile'),
    path('settings/profile/edit', views.edit_profile_view, name='edit_profile'),
    path('settings/profile/changePassword', views.change_password_view, name='change_password'),

    path('settings/users', views.users_list_view, name='users_list'),
    path('settings/users/add', views.create_user_view, name='create_user'),
    path('settings/users/<int:user_id>', views.user_view, name='user'),
    path('settings/users/<int:user_id>/edit', views.user_edit_view, name='edit_user'),
    path('settings/users/<int:user_id>/resetPassword', views.user_password_reset, name='user_password_reset'),
    path('settings/users/<int:user_id>/delete', views.delete_user_view, name='delete_user'),

    path('settings/groups', views.groups_list_view, name='groups_list'),
    path('settings/groups/add', views.add_group_view, name='add_group'),
    path('settings/groups/<int:group_id>', views.group_view, name='group'),


    path('api/inventory/tags/search', tag_search_view),
    path('api/inventory/tags/add', tag_add_view),
]
