from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_dashboard, name='sales_dashboard'),
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/quick-add/', views.quick_add_sale, name='quick_add_sale'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/return/', views.sale_return, name='sale_return'),
    path('sales/<int:pk>/delete/', views.delete_sale, name='delete_sale'),
    path('api/search-product/', views.search_product_api, name='search_product_api'),
]