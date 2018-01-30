from django.urls import path

from . import views
from .api_views.inventory import *

urlpatterns = [
    path('', views.home_view, name='home'),
    path('inventory/addDevice', views.add_device_view, name='add_device'),


    path('api/inventory/tags/search', tag_search_view),
    path('api/inventory/tags/add', tag_add_view),
]
