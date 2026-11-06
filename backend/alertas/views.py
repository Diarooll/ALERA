from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from usuarios.permissions import EhAdministrador

from .models import HistoricoNivel
from .serializers import EmitirAlertaSerializer, HistoricoSerializer
from .servicos import mudar_nivel

ULTIMOS = 20


class Alertas(APIView):
    """Painel ALERA: emite o alerta de verdade (muda o nível) e lista os últimos."""

    permission_classes = [EhAdministrador]

    def get(self, request):
        historico = HistoricoNivel.objects.select_related('area', 'responsavel')[:ULTIMOS]
        return Response(HistoricoSerializer(historico, many=True).data)

    def post(self, request):
        pedido = EmitirAlertaSerializer(data=request.data)
        pedido.is_valid(raise_exception=True)
        dados = pedido.validated_data

        gravados = [
            mudar_nivel(
                area,
                dados['nivel'],
                HistoricoNivel.Origem.DEFESA_CIVIL,
                request.user,
                mensagem=dados['mensagem'],
            )
            for area in dados['areas']
        ]
        novos = [h for h in gravados if h]
        return Response(HistoricoSerializer(novos, many=True).data, status=status.HTTP_201_CREATED)
