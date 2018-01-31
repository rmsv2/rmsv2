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

    path('inventory/categories/add', views.create_category_view, name='create_category'),
    path('inventory/categories/<int:category_id>', views.category_view, name='category'),
    path('inventory/categories/<int:category_id>/edit', views.edit_category_view, name='edit_category'),
    path('inventory/categories/<int:category_id>/delete', views.remove_category_view, name='delete_category'),


    path('api/inventory/tags/search', tag_search_view),
    path('api/inventory/tags/add', tag_add_view),
]
