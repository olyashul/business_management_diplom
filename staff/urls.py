from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('', views.staff_dashboard, name='staff_dashboard'),
    
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path('employees/<int:pk>/edit/', views.edit_employee, name='edit_employee'),
    path('employees/<int:pk>/delete/', views.delete_employee, name='delete_employee'),
    
    path('shifts/create/', views.create_schedule, name='create_schedule'),
    path('shifts/quick-add/', views.quick_add_shift, name='quick_add_shift'),
    path('shifts/<int:pk>/delete/', views.delete_shift_ajax, name='delete_shift_ajax'),
]