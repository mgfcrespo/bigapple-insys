from django.urls import path
from django.conf.urls import include, url
from .import views
from django.views.generic import TemplateView

app_name='inventory'
urlpatterns = [
    #supplier items
    path('supplier_item_add/', views.supplier_item_add, name='supplier_item_add'),
    path('supplier_item_list/', views.supplier_item_list, name='supplier_item_list'),
    path('supplier_item_edit/<int:id>/', views.supplier_item_edit, name='supplier_item_edit'),
    path('supplier_item_delete/<int:id>/', views.supplier_item_delete, name='supplier_item_delete'),
    #material requisition
    path('materials_requisition_form/', views.materials_requisition_form, name='materials_requisition_form'),
    path('materials_requisition_list/', views.materials_requisition_list, name='materials_requisition_list'),
    path('materials_requisition_details/<int:id>/', views.materials_requisition_details, name='materials_requisition_details'),
    #inventory 
    path('inventory_list/', views.inventory_list, name='inventory_list'),
    path('inventory_edit/<int:id>/', views.inventory_edit, name='inventory_edit'),
];