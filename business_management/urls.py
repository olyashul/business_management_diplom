"""
******************************************************************
Выпускная квалификационная работа по теме:
РАЗРАБОТКА КОРПОРАТИВНОЙ ИНФОРМАЦИОННОЙ СИСТЕМЫ ДЛЯ УПРАВЛЕНИЯ
ДЕЯТЕЛЬНОСТЬЮ ТОРГОВОГО ПРЕДПРИЯТИЯ

Язык программирования: Python
Веб-фреймворк: Django
СУБД: PostgreSQL
Среда разработки: Visual Studio Code
Разработала: Шульгина О.П.
Группа: ТИП-82
Год: 2026

Задачи системы:
1) Обеспечить авторизацию и регистрацию пользователей;
2) Реализовать ведение каталога товаров с поиском и фильтрацией;
3) Обеспечить оформление продаж и возвратов с формированием чека;
4) Реализовать управление сотрудниками и составление графиков работы;
5) Обеспечить выгрузку отчетов в формате Excel.
******************************************************************
Файл: business_management/urls.py

Маршруты (URL-пути):
admin/ - панель администратора Django;
/ (пустая строка) - главная страница (перенаправление на профиль);
accounts/ - все маршруты приложения accounts (регистрация, вход, профиль);
main/ - маршруты главной страницы (задачи, дата, смена);
products/ - маршруты каталога товаров и поставщиков;
staff/ - маршруты управления персоналом и графиками работы;
sales/ - маршруты продаж и возвратов;
reports/ - маршруты генерации отчетов в Excel.
******************************************************************
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import home_view  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view,  name='main'),
    path('accounts/', include('accounts.urls')),
    path('main/', include('main.urls', namespace='main')),
    path('products/', include('products.urls')), 
    path('staff/', include('staff.urls')), 
    path('sales/', include('sales.urls')),
    path('reports/', include('reports.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, 
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, 
                          document_root=settings.STATIC_ROOT)