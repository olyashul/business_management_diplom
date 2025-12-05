# business_management/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import home_view  # Импортируем из accounts.views

urlpatterns = [
    # Админка Django
    path('admin/', admin.site.urls),
    
    # Главная страница
    path('', home_view,  name='main'),
    
    # Маршруты для аккаунтов
    path('accounts/', include('accounts.urls')),
    # Маршруты для main (dashboard, задачи и т.д.)
    path('main/', include('main.urls', namespace='main')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, 
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, 
                          document_root=settings.STATIC_ROOT)