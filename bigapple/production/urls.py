from django.urls import path
from django.conf.urls import include, url
from . import views

app_name='production'
urlpatterns = [
        url(r'^production_details/', views.production_details, name='production_details')
];