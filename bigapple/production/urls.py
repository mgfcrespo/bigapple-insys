from django.urls import path
from django.conf.urls import include, url
from .import views

app_name='production'
urlpatterns = [
        url(r'^production_details/', views.production_details, name='production_details'),
        path('overall-production-schedule/', views.production_schedule, name='production_schedule'),

        #Job Order
        path('job-order-list/', views.job_order_list, name='job_order_list'),
        path('job-order-details/<int:id>', views.job_order_details, name='job_order_details'),
        path('finished-job-order-list/', views.finished_job_order_list_view, name='finished_job_order_list'),
        path('add-extruder-schedule/<int:id>', views.add_extruder_schedule, name='add_extruder_schedule'),
        path('add-printing-schedule/<int:id>', views.add_printing_schedule, name='add_printing_schedule'),
        path('add-cutting-schedule/<int:id>', views.add_cutting_schedule, name='add_cutting_schedule'),
        path('add-laminating-schedule/<int:id>', views.add_laminating_schedule, name='add_laminating_schedule'),

        path('extruder-machine-schedule/', views.extruder_machine_schedule, name='extruder_machine_schedule'),
        path('printing-machine-schedule/', views.printing_machine_schedule, name='printing_machine_schedule'),
        path('laminating-machine-schedule/', views.laminating_machine_schedule, name='laminating_machine_schedule'),
        path('cutting-machine-schedule/', views.cutting_machine_schedule, name='cutting_machine_schedule'),

        path('production-report/', views.production_report, name='production_report'),
        path('shift-schedule/', views.shift_schedule, name='shift_schedule'),
        path('weekly-schedule/', views.weekly_schedule, name='weekly_schedule'),
        path('sched-test/', views.sched_test, name='sched_test'),



];