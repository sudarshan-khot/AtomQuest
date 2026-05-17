"""
URL configuration for atomquest project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('portal.urls')),
    path('api-auth/', include('rest_framework.urls')),
    # Token auth endpoint used by the frontend
    path('api-token-auth/', obtain_auth_token, name='api-token-auth'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
