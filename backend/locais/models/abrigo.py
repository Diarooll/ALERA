from django.db import models

from .area_risco import AreaRisco
from .tipo_abrigo import TipoAbrigo


class Abrigo(models.Model):
    class Situacao(models.TextChoices):
        ABERTO = 'aberto', 'Aberto'
        POUCAS_VAGAS = 'poucas', 'Poucas vagas'
        SO_ALERTA = 'so-alerta', 'Só em nível de alerta'
        FECHADO = 'fechado', 'Fechado'

    nome = models.CharField(max_length=150)
    tipo = models.ForeignKey(
        TipoAbrigo, on_delete=models.PROTECT, null=True, blank=True, related_name='abrigos'
    )
    referencia = models.CharField('referência', max_length=150, blank=True)
    # O abrigo não pertence mais a uma área: o morador escolhe o que fica mais perto
    area = models.ForeignKey(
        AreaRisco,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='abrigos',
        verbose_name='área de risco',
    )
    situacao = models.CharField(
        'situação', max_length=10, choices=Situacao.choices, default=Situacao.ABERTO
    )
    # Posição no mapa: o admin clica no mapa do painel. Latitude e longitude andam juntas
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    capacidade = models.PositiveIntegerField('capacidade (vagas)', null=True, blank=True)
    # Antigos, digitados à mão. Agora a distância é calculada para cada morador (locais.servicos)
    distancia_m = models.PositiveIntegerField('distância em metros', null=True, blank=True)
    tempo_a_pe_min = models.PositiveIntegerField('minutos a pé', null=True, blank=True)
    passos_rota = models.TextField('passos da rota', blank=True, help_text='Um passo por linha.')
    rua_a_evitar = models.CharField('rua a evitar', max_length=150, blank=True)
    desenho_mapa = models.TextField('desenho do mapa', blank=True)

    class Meta:
        ordering = ['nome']
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(latitude__isnull=True, longitude__isnull=True)
                    | models.Q(latitude__isnull=False, longitude__isnull=False)
                ),
                name='abrigo_lat_lng_juntas',
            ),
        ]

    def __str__(self):
        return self.nome
