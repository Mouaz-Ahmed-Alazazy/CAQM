from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from caqm_project.views import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('admins/', include('admins.urls')),
    path('appointments/', include('appointments.urls')),
    path('patients/', include('patients.urls')),
    path('doctors/', include('doctors.urls')),
    path('queues/', include('queues.urls')),
    path('nurses/', include('nurses.urls')),
    path('', lambda request: redirect('accounts:login')),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'caqm_project.views.custom_404'
handler500 = 'caqm_project.views.custom_500'
handler403 = 'caqm_project.views.custom_403'
