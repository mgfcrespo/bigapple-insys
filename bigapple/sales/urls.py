from django.urls import path
from django.conf.urls import include, url
from .import views
from django.views.generic import TemplateView

app_name='sales'
urlpatterns = [

			path('sales-exception-report/', views.sales_exception_report, name='sales_exception_report'),

			#PO urls
			path('po-list-view/', views.po_list_view, name='po-list-view'),
			path('po-list-view/PO<int:pk>/', views.po_detail_view, name='po-detail-view'),
			path('create-client-po-form/', views.create_client_po, name='create-client-po-form'),
			path('confirm-client-po/<int:pk>/', views.confirm_client_po, name='confirm-client-po'),

			#sales_invoice urls
			path('sales-invoice-list/', views.invoice_list_view, name='sales_invoice_list'),
			path('sales-invoice-details/<int:pk>/', views.invoice_detail_view, name='sales_invoice_details'),
			path('sales-invoice-details/<int:pk>/', views.invoice_detail_view, name='add_payment_form'),
			path('sales-statement-of-accounts/', views.statement_of_accounts_list_view, name='statement_of_accounts'),

			#client credit urls
			path('client-payment-list/', views.payment_list_view, name='client_payment_list'),
			path('client-payment-details/invoice<int:pk>/', views.payment_detail_view, name='client_payment_details'),

			#rush order urls
			path('rush-order-list/', views.rush_order_list, name='rush_order_list'),
			path('rush-order-assessment/<int:pk>/', views.rush_order_assessment, name='rush_order_assessment'),

		    #supplier urls
			path('supplier-list/', views.supplier_list, name='supplier_list'),
			path('supplier-add/', views.supplier_add, name='supplier_add'),
			path('supplier-edit/<int:id>/', views.supplier_edit, name='supplier_edit'),
			path('supplier-delete/<int:id>/', views.supplier_delete, name='supplier_delete'),

			#client urls
			path('client-add/', views.client_add, name='client_add'),
			path('client-edit/<int:id>/', views.client_edit, name='client_edit'),
			path('client-list/', views.client_list, name='client_list'),

			#employee urls
			path('employee-add/', views.employee_add, name='employee_add'),
			path('employee-list/', views.employee_list, name='employee_list'),
			path('employee-details/<int:id>/', views.employee_details, name='employee_details'),
			path('employee-edit/<int:id>/', views.employee_edit, name='employee_edit'),
			path('employee-delete/<int:id>/', views.employee_delete, name='employee_delete'),

			#demand forecast
			path('client-demand-forecast/', views.demand_forecast, name='demand_forecast'),
			path('client-demand-forecast/<int:id>/', views.demand_forecast_details, name='demand_forecast_details'),
];
