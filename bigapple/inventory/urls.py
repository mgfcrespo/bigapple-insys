from django.urls import path
from django.conf.urls import include, url
from .import views
from django.views.generic import TemplateView

app_name='inventory'
urlpatterns = [
    #inventory items
    path('inventory_item_add/', views.inventory_item_add, name='inventory_item_add'),
    path('inventory_item_list/', views.inventory_item_list, name='inventory_item_list'),
    path('inventory_item_edit/<int:id>/', views.inventory_item_edit, name='inventory_item_edit'),
    path('inventory_item_delete/<int:id>/', views.inventory_item_delete, name='inventory_item_delete'),
    #material requisition
    path('materials_requisition_form/', views.materials_requisition_form, name='materials_requisition_form'),
    path('materials_requisition_list/', views.materials_requisition_list, name='materials_requisition_list'),
    path('materials_requisition_details/<int:id>/', views.materials_requisition_details, name='materials_requisition_details'),
	path('materials_requisition_approval/<int:id>/', views.materials_requisition_approval, name='materials_requisition_approval'),
	#material requisition
    path('purchase_requisition_form/', views.purchase_requisition_form, name='purchase_requisition_form'),
    path('purchase_requisition_list/', views.purchase_requisition_list, name='purchase_requisition_list'),
    path('purchase_requisition_details/<int:id>/', views.purchase_requisition_details, name='purchase_requisition_details'),
	path('purchase_requisition_approval/<int:id>/', views.purchase_requisition_approval, name='purchase_requisition_approval'),
    #SupplierPO
    path('supplierPO_form/', views.supplierPO_form, name='supplierPO_form'),
];