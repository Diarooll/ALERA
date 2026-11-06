from rest_framework import generics, permissions
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CadastroSerializer, LoginSerializer, MeuPerfilSerializer


class CadastroView(generics.CreateAPIView):
    serializer_class = CadastroSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'cadastro'


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


class MeuPerfilView(generics.RetrieveUpdateAPIView):
    serializer_class = MeuPerfilSerializer
    http_method_names = ['get', 'patch', 'head', 'options']
    throttle_scope = 'perfil'

    def get_throttles(self):
        # Só a mudança tem limite (por conta). Ler fica livre: o app confere o nível a cada minuto
        return [ScopedRateThrottle()] if self.request.method == 'PATCH' else []

    def get_object(self):
        return self.request.user
