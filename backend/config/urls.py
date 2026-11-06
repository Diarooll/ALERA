from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/saude/', views.saude, name='saude'),
    path('api/', include('usuarios.urls')),
    path('api/', include('locais.urls')),
    path('api/', include('alertas.urls')),
]
