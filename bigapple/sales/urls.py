from django.urls import path
from django.conf.urls import include, url
from .import views
from django.views.generic import TemplateView

app_name='sales'
urlpatterns = [
          path('po-list-view/', views.POListView.as_view(), name='po-list-view'),
          path('po-list-view/PO<int:pk>/', views.PODetailView.as_view(), name='po-detail-view'),
          path('create-client-po-form/', views.create_client_po, name='create-client-po-form'),
          path('po-list-view/', views.POListView.as_view(), name='po-list-view'),
          path('create-client-po-form/', views.create_client_po, name='create-client-po-form'),
          #supplier urls
          path('supplier_list/', views.supplier_list, name='supplier_list'),
          path('supplier_add/', views.supplier_add, name='supplier_add'),
          path('supplier_edit/<int:id>/', views.supplier_edit, name='supplier_edit'),
          path('supplier_delete/<int:id>/', views.supplier_delete, name='supplier_delete'),
          #sales_invoice urls
          path('sales_invoice_list/', views.sales_invoice_list, name='sales_invoice_list'),
          path('sales_invoice_details/<int:id>/', views.sales_invoice_details, name='sales_invoice_details'),
		  #JO urls
          path('JO_list/', views.JO_list, name='JO_list'),
          path('JO_details/<int:id>/', views.JO_details, name='JO_details'),
        # client credit urls
          path('client_credit_list/', views.client_credit_list, name='sales_client_credit_list'),
          path('client_credit_details/<int:id>/', views.client_credit_details, name='sales_client_credit_details'),
        # rush order urls
          path('rush_order_list/', views.rush_order_list, name='sales_rush_order_list'),
];
