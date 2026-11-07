from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.utils import get_md5_hash_password
from rest_framework_simplejwt.views import TokenObtainPairView, TokenViewBase

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


class LimiteDaSessao(SimpleRateThrottle):
    """Renovar e sair: 30 por minuto por IP, contado à parte do login.

    Quem usa o app renova umas três vezes por hora. A folga aguenta muita gente atrás do
    mesmo IP (rede da prefeitura, operadora de celular) e ainda barra quem martela a rota.
    """

    scope = 'sessao'
    rate = '30/min'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class RenovarSerializer(serializers.Serializer):
    """Troca o token de renovação por um par novo. O usado vai para a lista negra."""

    # Os nomes da API do ALERA: entra "renovacao", sai "token" + "renovacao"
    renovacao = serializers.CharField(write_only=True)

    def validate(self, dados):
        # Vencido, falso, de acesso ou já usado: TokenError, que a view devolve como 401
        renovacao = RefreshToken(dados['renovacao'])

        usuario = (
            get_user_model()
            .objects.filter(**{api_settings.USER_ID_FIELD: renovacao.get(api_settings.USER_ID_CLAIM)})
            .first()
        )
        # Conta apagada ou desativada pelo ADM não ganha token novo
        if usuario is None or not usuario.is_active:
            raise AuthenticationFailed('Esta conta não está ativa.', 'no_active_account')
        # A senha mudou depois que esta sessão abriu: precisa entrar de novo
        if renovacao.get(api_settings.REVOKE_TOKEN_CLAIM) != get_md5_hash_password(usuario.password):
            raise AuthenticationFailed('A senha mudou. Entre de novo.', 'password_changed')

        acesso = renovacao.access_token
        # Rodízio: o usado vai para a lista negra e sai um novo, com o prazo contado de novo.
        # Igual ao do simplejwt, mas com o prazo de cada tipo de conta (ver LoginSerializer)
        renovacao.blacklist()
        renovacao.set_jti()
        renovacao.set_exp(lifetime=LoginSerializer.prazo_da_sessao(usuario))
        renovacao.set_iat()
        renovacao.outstand()
        return {'token': str(acesso), 'renovacao': str(renovacao)}


class RenovarView(TokenViewBase):
    """POST {renovacao} -> {token, renovacao}. Não pede o token de acesso, que já pode ter vencido."""

    serializer_class = RenovarSerializer
    throttle_classes = [LimiteDaSessao]


class SairSerializer(TokenBlacklistSerializer):
    refresh = None
    renovacao = serializers.CharField(write_only=True)

    def validate(self, dados):
        return super().validate({'refresh': dados['renovacao']})


class SairView(TokenViewBase):
    """POST {renovacao}: encerra a sessão deste aparelho. O token de renovação para de valer na hora.

    O de acesso, que vive no máximo 20 minutos, o próprio app descarta.
    """

    serializer_class = SairSerializer
    throttle_classes = [LimiteDaSessao]

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeuPerfilView(generics.RetrieveUpdateAPIView):
    serializer_class = MeuPerfilSerializer
    http_method_names = ['get', 'patch', 'head', 'options']
    throttle_scope = 'perfil'

    def get_throttles(self):
        # Só a mudança tem limite (por conta). Ler fica livre: o app confere o nível a cada minuto
        return [ScopedRateThrottle()] if self.request.method == 'PATCH' else []

    def get_object(self):
        return self.request.user
