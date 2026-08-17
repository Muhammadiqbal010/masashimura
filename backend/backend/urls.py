from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('menu.urls')),
    path('api/', include('order.urls')),
    path('api/homepage/', include('homepage.urls')),
    path('api/', include('finance.urls')),
    path('api/', include('prediction.urls')),
    path('api/', include('promotions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)