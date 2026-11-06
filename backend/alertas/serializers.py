from rest_framework import serializers

from locais.models import AreaRisco, Nivel

from .models import HistoricoNivel


class EmitirAlertaSerializer(serializers.Serializer):
    areas = serializers.PrimaryKeyRelatedField(
        queryset=AreaRisco.objects.all(), many=True, allow_empty=False
    )
    nivel = serializers.ChoiceField(choices=Nivel.choices)
    mensagem = serializers.CharField(max_length=300, allow_blank=True, required=False, default='')


class HistoricoSerializer(serializers.ModelSerializer):
    area = serializers.CharField(source='area.nome')
    responsavel = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoNivel
        fields = ['id', 'area', 'nivel_anterior', 'nivel_novo', 'origem', 'mensagem', 'responsavel', 'criado_em']

    def get_responsavel(self, historico):
        return historico.responsavel.email if historico.responsavel else None
