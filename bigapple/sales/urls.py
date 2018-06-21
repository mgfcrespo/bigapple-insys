from django.urls import path
from django.conf.urls import include, url
from .import views
from django.views.generic import TemplateView

app_name='sales'
urlpatterns = [
  path('add_supplier/', views.add_supplier, name='add_supplier'),
  path('supplier_list/', views.supplier_list, name='supplier_list'),
  url(r'^supplier_details/(?P<pk>\d+)/$', views.supplier_details, name ='supplier_details'),
  url(r'^edit_supplier/(?P<pk>\d+)/$', views.edit_supplier, name ='edit_supplier'),
  url(r'^delete_supplier/(?P<pk>\d+)/$', views.delete_supplier, name ='delete_supplier'),
  
  #path('edit_supplier/<int:id>/', views.edit_supplier, name='edit_supplier'),
  #path('delete_supplier/<int:id>/', views.delete_supplier, name='delete_supplier'),
  #url(r'^edit_supplier/(?P<id>\d+/)/$', views.edit_supplier, name='edit_supplier'),
  #path('sales_details/', views.sales_details, name='sales_details'),
  #path('', TemplateView.as_view(template_name='index.html')),
  #path('client-po-form-add/', views.POFormCreateView.as_view(), name='client-po-form-add')
  #path('client-po-list-view/', views.POListView.as_view(), name='client-po-list-view')
  #path('<int:pk>/view-clientPO-details/', views.PODetailView.as_view(), name='po_detail'),
]
