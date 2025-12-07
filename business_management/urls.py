# business_management/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import home_view  # Импортируем из accounts.views

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