from django.urls import path
from django.conf.urls import include, url
from . import views
from django.views.generic import TemplateView

app_name='sales'
urlpatterns = [
          url(r'^sales_details/', views.sales_details, name='sales_details'),
          #path('client-po-form-add/', views.display_client_po, name='client-po-form-add')
          #path('client-po-list-view/', views.POListView.as_view(), name='client-po-list-view')
          #path('<int:pk>/view-clientPO-details/', views.PODetailView.as_view(), name='po_detail'),
          #path('add_supplier/', views.add_supplier, name='add_supplier'),
          #path('sales_details/', views.sales_details, name='sales_details'),
          path('po-list-view/', views.POListView.as_view(), name='po-list-view'),
          path('client-po-form-add/', views.display_client_po, name='client-po-form-add')
          #path('client-po-list-view/', views.POListView.as_view(), name='client-po-list-view')
          #path('<int:pk>/view-clientPO-details/', views.PODetailView.as_view(), name='po_detail'),
];
