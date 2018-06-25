from django.urls import path
from django.conf.urls import include, url
from .import views
from django.views.generic import TemplateView

app_name='sales'
urlpatterns = [
          url(r'^sales_details/', views.sales_details, name='sales_details'),
          path('po-list-view/', views.POListView.as_view(), name='po-list-view'),
          path('po-list-view/PO<int:pk>/', views.PODetailView.as_view(), name='po-detail-view'),
          path('create-client-po-form/', views.create_client_po, name='create-client-po-form'),

];



