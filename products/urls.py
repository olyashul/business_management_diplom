from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Каталог
    path('', views.catalog_dashboard, name='catalog_dashboard'),
    path('list/', views.product_list, name='product_list'),
    path('categories/', views.category_list, name='category_list'),
    
    # Товары
    path('create/', views.product_create, name='product_create'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/edit/', views.product_update, name='product_update'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('<int:pk>/update-stock/', views.update_stock, name='update_stock'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
]