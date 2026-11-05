from decimal import Decimal

from rest_framework import serializers

from . import servicos
from .models import Abrigo, AreaRisco, TipoAbrigo

LATITUDE = {'max_digits': 9, 'decimal_places': 6, 'coerce_to_string': False}


class TipoAbrigoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAbrigo
        fields = ['id', 'nome', 'icone']


class AreaRiscoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaRisco
        fields = ['id', 'nome', 'nivel', 'nivel_atualizado_em']
        read_only_fields = fields


class AbrigoSerializer(serializers.ModelSerializer):
    tipo = serializers.PrimaryKeyRelatedField(queryset=TipoAbrigo.objects.all())
    latitude = serializers.DecimalField(
        min_value=Decimal('-90'), max_value=Decimal('90'), **LATITUDE
    )
    longitude = serializers.DecimalField(
        min_value=Decimal('-180'), max_value=Decimal('180'), **LATITUDE
    )
    # Calculadas para quem está logado: linha reta da casa dele até o abrigo
    distancia_m = serializers.SerializerMethodField()
    tempo_a_pe_min = serializers.SerializerMethodField()

    class Meta:
        model = Abrigo
        fields = [
            'id',
            'nome',
            'tipo',
            'referencia',
            'situacao',
            'latitude',
            'longitude',
            'capacidade',
            'distancia_m',
            'tempo_a_pe_min',
        ]

    def to_representation(self, abrigo):
        dados = super().to_representation(abrigo)
        dados['tipo'] = TipoAbrigoSerializer(abrigo.tipo).data if abrigo.tipo else None
        return dados

    def _distancia(self, abrigo):
        usuario = self.context['request'].user
        if None in (usuario.latitude, usuario.longitude, abrigo.latitude, abrigo.longitude):
            return None
        return servicos.distancia_em_metros(
            usuario.latitude, usuario.longitude, abrigo.latitude, abrigo.longitude
        )

    def get_distancia_m(self, abrigo):
        return self._distancia(abrigo)

    def get_tempo_a_pe_min(self, abrigo):
        metros = self._distancia(abrigo)
        return None if metros is None else servicos.tempo_a_pe_min(metros)
