from django.urls import path
from django.conf.urls import include, url
from .import views
from django.views.generic import TemplateView

app_name='inventory'
urlpatterns = [
    #inventory items
    path('inventory-item-add/', views.inventory_item_add, name='inventory_item_add'),
    path('inventory-item-list/', views.inventory_item_list, name='inventory_item_list'),
    path('inventory-item-edit/<int:id>/', views.inventory_item_edit, name='inventory_item_edit'),
    path('inventory-item-delete/<int:id>/', views.inventory_item_delete, name='inventory_item_delete'),
    #supplier raw material
    path('supplier-rawmat-add/', views.supplier_rawmat_add, name='supplier_rawmat_add'),
    path('supplier-details-list/<int:id>/', views.supplier_details_list, name='supplier_details_list'),
    path('supplier-rawmat-edit/<int:id>/', views.supplier_rawmat_edit, name='supplier_rawmat_edit'),
    path('supplier-rawmat-delete/<int:id>/', views.supplier_rawmat_delete, name='supplier_rawmat_delete'),
    #material requisition
    path('materials-requisition-list/', views.materials_requisition_list, name='materials_requisition_list'),
    path('materials-requisition-details/<int:id>/', views.materials_requisition_details, name='materials_requisition_details'),
    path('materials-requisition-approval/<int:id>/', views.materials_requisition_approval, name='materials_requisition_approval'),
    #purcahase requisition
    path('purchase-requisition-form/', views.purchase_requisition_form, name='purchase_requisition_form'),
    path('purchase-requisition-list/', views.purchase_requisition_list, name='purchase_requisition_list'),
    path('purchase-requisition-details/<int:id>/', views.purchase_requisition_details, name='purchase_requisition_details'),
    path('purchase-requisition-approval/<int:id>/', views.purchase_requisition_approval, name='purchase_requisition_approval'),
    #inventory Count
    path('inventory-count-form/', views.inventory_count_form, name='inventory_count_form'),
    path('inventory-count-form/<int:id>/', views.inventory_count_form, name='inventory_count_form'),
    path('inventory-count-list/<int:id>/', views.inventory_count_list, name='inventory_count_list'),
    #SupplierPO
    path('supplierPO-form/', views.supplierPO_form, name='supplierPO_form'),
    path('supplierPO-list/', views.supplierPO_list, name='supplierPO_list'),
    path('supplierPO-details/<int:id>/', views.supplierPO_details, name='supplierPO_details'),
    path('ajax/load-items/', views.load_items, name='ajax_load_items'),
];