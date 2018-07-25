from django.urls import path
from django.conf.urls import include, url
from .import views
from django.views.generic import TemplateView

app_name='sales'
urlpatterns = [
          #PO urls
          path('po-list-view/', views.POListView.as_view(), name='po-list-view'),
          path('po-list-view/PO<int:pk>/', views.PODetailView.as_view(), name='po-detail-view'),
          path('create-client-po-form/', views.create_client_po, name='create-client-po-form'),

          #JO urls
          path('JO-list/', views.JOListView.as_view(), name='JO_list'),
          path('JO-details/JO<int:pk>/', views.JODetailView.as_view(), name='JO_details'),

          #sales_invoice urls
          path('sales-invoice-list/', views.InvoiceListView.as_view(), name='sales_invoice_list'),
          path('sales-invoice-details/<int:pk>/', views.invoice_detail_view, name='sales_invoice_details'),
          path('sales-invoice-details/<int:pk>', views.invoice_detail_view, name='add_payment_form'),

          #client credit urls
          path('client-payment-list/', views.payment_list_view, name='client_payment_list'),
          path('client-payment-details/<int:pk>/', views.payment_detail_view, name='client_payment_details'),

          #rush order urls
          path('rush-order-list/', views.rush_order_list, name='sales_rush_order_list'),

          #supplier urls
          path('supplier-list/', views.supplier_list, name='supplier_list'),
          path('supplier-add/', views.supplier_add, name='supplier_add'),
          path('supplier-edit/<int:id>/', views.supplier_edit, name='supplier_edit'),
          path('supplier-delete/<int:id>/', views.supplier_delete, name='supplier_delete'),

];
