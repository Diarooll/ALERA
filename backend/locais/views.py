from django.db.models import ProtectedError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from usuarios.permissions import EhAdministrador

from .models import Abrigo, AreaRisco, TipoAbrigo
from .serializers import AbrigoSerializer, AreaRiscoSerializer, TipoAbrigoSerializer


class LeituraLogadoEscritaAdmin:
    """Qualquer pessoa logada lê; só administrador cria, muda ou apaga."""

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated()]
        return [EhAdministrador()]


class AbrigoLista(LeituraLogadoEscritaAdmin, generics.ListCreateAPIView):
    queryset = Abrigo.objects.select_related('tipo')
    serializer_class = AbrigoSerializer

    def list(self, request, *args, **kwargs):
        resposta = super().list(request, *args, **kwargs)
        # Do mais perto ao mais longe. Sem localização da casa, fica em ordem de nome
        resposta.data = sorted(
            resposta.data,
            key=lambda a: (a['distancia_m'] is None, a['distancia_m'] or 0, a['nome']),
        )
        return resposta


class AbrigoDetalhe(LeituraLogadoEscritaAdmin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Abrigo.objects.select_related('tipo')
    serializer_class = AbrigoSerializer


class TipoAbrigoLista(LeituraLogadoEscritaAdmin, generics.ListCreateAPIView):
    queryset = TipoAbrigo.objects.all()
    serializer_class = TipoAbrigoSerializer


# Áreas de risco são só do painel: o morador nunca vê as bolinhas


class AreaRiscoLista(generics.ListCreateAPIView):
    permission_classes = [EhAdministrador]
    queryset = AreaRisco.objects.prefetch_related('circulos')
    serializer_class = AreaRiscoSerializer


class AreaRiscoDetalhe(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [EhAdministrador]
    queryset = AreaRisco.objects.prefetch_related('circulos')
    serializer_class = AreaRiscoSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            # O histórico guarda quem emitiu cada alerta: área com alerta não some
            return Response(
                {
                    'detail': 'Esta área já teve alertas e não pode ser apagada. '
                    'Você pode renomear a área ou tirar as bolinhas dela.'
                },
                status=status.HTTP_409_CONFLICT,
            )
