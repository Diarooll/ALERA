from django.urls import path

from .views import CadastroView, LoginView, MeuPerfilView, RenovarView, SairView

urlpatterns = [
    path('auth/cadastro/', CadastroView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('auth/renovar/', RenovarView.as_view()),
    path('auth/sair/', SairView.as_view()),
    path('me/', MeuPerfilView.as_view()),
]
