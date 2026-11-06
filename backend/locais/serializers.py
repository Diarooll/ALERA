from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from . import servicos
from .models import RAIO_MAXIMO_M, RAIO_MINIMO_M, Abrigo, AreaRisco, CirculoRisco, TipoAbrigo

LATITUDE = {'max_digits': 9, 'decimal_places': 6, 'coerce_to_string': False}


# Campos de posição no mapa, iguais em abrigos, bolinhas e na casa do morador
def campo_latitude(**extra):
    return serializers.DecimalField(
        min_value=Decimal('-90'), max_value=Decimal('90'), **LATITUDE, **extra
    )


def campo_longitude(**extra):
    return serializers.DecimalField(
        min_value=Decimal('-180'), max_value=Decimal('180'), **LATITUDE, **extra
    )


class TipoAbrigoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAbrigo
        fields = ['id', 'nome', 'icone']


class CirculoSerializer(serializers.ModelSerializer):
    latitude = campo_latitude()
    longitude = campo_longitude()
    raio_m = serializers.IntegerField(min_value=RAIO_MINIMO_M, max_value=RAIO_MAXIMO_M)

    class Meta:
        model = CirculoRisco
        fields = ['latitude', 'longitude', 'raio_m']


class AreaRiscoSerializer(serializers.ModelSerializer):
    """O painel cria e desenha a área. O nível só muda pelo alerta (alertas.servicos)."""

    circulos = CirculoSerializer(many=True, required=False)

    class Meta:
        model = AreaRisco
        fields = ['id', 'nome', 'nivel', 'nivel_atualizado_em', 'orientacao', 'circulos']
        read_only_fields = ['nivel', 'nivel_atualizado_em', 'orientacao']

    @transaction.atomic
    def create(self, dados):
        circulos = dados.pop('circulos', [])
        area = AreaRisco.objects.create(**dados)
        self._trocar_circulos(area, circulos)
        return area

    @transaction.atomic
    def update(self, area, dados):
        circulos = dados.pop('circulos', None)
        area = super().update(area, dados)
        # As bolinhas chegam todas juntas e substituem as antigas
        if circulos is not None:
            self._trocar_circulos(area, circulos)
        return area

    def _trocar_circulos(self, area, circulos):
        area.circulos.all().delete()
        CirculoRisco.objects.bulk_create(CirculoRisco(area=area, **c) for c in circulos)


class AbrigoSerializer(serializers.ModelSerializer):
    tipo = serializers.PrimaryKeyRelatedField(queryset=TipoAbrigo.objects.all())
    latitude = campo_latitude()
    longitude = campo_longitude()
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
