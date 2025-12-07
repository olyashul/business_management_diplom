from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('quick-financial/', views.quick_financial_report, name='quick_financial_report'),
    path('quick-products/', views.quick_products_report, name='quick_products_report'),
    path('quick-schedule/', views.quick_schedule_report, name='quick_schedule_report'),
    path('quick-daily/', views.quick_daily_report, name='quick_daily_report'),
]