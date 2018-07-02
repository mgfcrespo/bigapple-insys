from django.urls import path
from django.conf.urls import include, url
from .import views
from django.views.generic import TemplateView

app_name='inventory'
urlpatterns = [
    path('supplier_rm_add/', views.supplier_rm_add, name='supplier_rm_add'),
    path('supplier_item_list/', views.supplier_item_list, name='supplier_item_list'),
    path('supplier_item_edit/<int:id>/', views.supplier_item_edit, name='supplier_item_edit'),
    path('supplier_item_delete/<int:id>/', views.supplier_item_delete, name='supplier_item_delete'),
];