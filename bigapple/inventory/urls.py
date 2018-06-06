from django.urls import path
from django.conf.urls import include, url
from . import views

app_name='inventory'
urlpatterns = [
        url(r'^inventory_details/', views.inventory_details, name='inventory_details')
];