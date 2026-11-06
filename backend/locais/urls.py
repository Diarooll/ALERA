from django.urls import path

from .views import AbrigoDetalhe, AbrigoLista, AreaRiscoDetalhe, AreaRiscoLista, TipoAbrigoLista

urlpatterns = [
    path('abrigos/', AbrigoLista.as_view()),
    path('abrigos/<int:pk>/', AbrigoDetalhe.as_view()),
    path('tipos-abrigo/', TipoAbrigoLista.as_view()),
    path('areas/', AreaRiscoLista.as_view()),
    path('areas/<int:pk>/', AreaRiscoDetalhe.as_view()),
]
