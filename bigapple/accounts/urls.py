from django.urls import path
from django.conf.urls import include, url
from . import views

app_name='accounts'
urlpatterns = [
        url(r'^account_details/', views.account_details, name='account_details')
];