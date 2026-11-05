from django.urls import path

from .views import CadastroView, LoginView, MeuPerfilView

urlpatterns = [
    path('auth/cadastro/', CadastroView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('me/', MeuPerfilView.as_view()),
]
