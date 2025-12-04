from django.urls import path
from . import views

app_name = 'accounts'  # Пространство имен

urlpatterns = [
    # Основные URL
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),  # Исправлено имя функции
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),  # Добавлен
    
    # HTMX URL для профиля
    path('profile/details/', views.account_details, name='account_details'),
    path('profile/edit/', views.edit_account_details, name='edit_account_details'),
    path('profile/update/', views.update_account_details, name='update_account_details'),
    
    # Дополнительные URL
    path('users/', views.user_list, name='user_list'),  # Только для администраторов
]