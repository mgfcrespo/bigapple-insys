from django.urls import path
from django.conf.urls import include, url
from . import views
from django.contrib import admin, auth
#from django.contrib.auth.views import auth_login, auth_logout, logout_then_login
from django.views.generic import TemplateView


app_name='accounts'
urlpatterns = [
    path('user-page-view/', views.user_page_view, name='user-page-view'),
    path('account_details/', views.account_details, name='account_details'),
    #path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout')
]



