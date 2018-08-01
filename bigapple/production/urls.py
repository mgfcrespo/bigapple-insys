from django.urls import path
from django.conf.urls import include, url
from .import views

app_name='production'
urlpatterns = [
        url(r'^production_details/', views.production_details, name='production_details'),
        path('overall-production-schedule/', views.production_schedule, name='production_schedule'),
		path('jo-approval/<int:id>', views.jo_approval, name='jo_approval'),
        #Job Order
        path('job-order-list/', views.job_order_list, name='job_order_list'),
        path('job-order-details/<int:id>', views.job_order_details, name='job_order_details'),
        path('add-extruder-schedule/<int:id>', views.add_extruder_schedule, name='add_extruder_schedule'),
        path('add-printing-schedule/<int:id>', views.add_printing_schedule, name='add_printing_schedule'),
        path('add-cutting-schedule/<int:id>', views.add_cutting_schedule, name='add_cutting_schedule'),
];