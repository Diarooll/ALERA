from django.urls import path

from .views import Alertas

urlpatterns = [
    path('alertas/', Alertas.as_view()),
]
