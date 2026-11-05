from django.conf import settings
from django.db import models

from locais.models import AreaRisco, Nivel


class Previsao(models.Model):
    area = models.ForeignKey(
        AreaRisco, on_delete=models.CASCADE, related_name='previsoes', verbose_name='área de risco'
    )
    chuva_mm_24h = models.DecimalField('chuva prevista em 24 h (mm)', max_digits=6, decimal_places=1)
    nivel_calculado = models.CharField('nível calculado', max_length=10, choices=Nivel.choices)
    fonte = models.CharField(max_length=60)
    recebida_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'previsão'
        verbose_name_plural = 'previsões'
        ordering = ['-recebida_em']
        indexes = [models.Index(fields=['area', '-recebida_em'], name='previsao_area_recente')]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(chuva_mm_24h__gte=0), name='previsao_chuva_positiva'
            ),
            # Perigo só é definido pela Defesa Civil, nunca pela previsão
            models.CheckConstraint(
                condition=models.Q(nivel_calculado__in=['normal', 'atencao', 'alerta']),
                name='previsao_nivel_automatico',
            ),
        ]

    def __str__(self):
        return f'{self.area}: {self.chuva_mm_24h} mm'


class HistoricoNivel(models.Model):
    class Origem(models.TextChoices):
        PREVISAO = 'previsao', 'Previsão'
        DEFESA_CIVIL = 'defesa-civil', 'Defesa Civil'

    area = models.ForeignKey(
        AreaRisco, on_delete=models.PROTECT, related_name='historico', verbose_name='área de risco'
    )
    nivel_anterior = models.CharField('nível anterior', max_length=10, choices=Nivel.choices)
    nivel_novo = models.CharField('nível novo', max_length=10, choices=Nivel.choices)
    origem = models.CharField(max_length=12, choices=Origem.choices)
    # PROTECT: conta de agente com histórico é desativada, não apagada, para não perder o responsável
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='mudancas_de_nivel',
        verbose_name='responsável',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'histórico de nível'
        verbose_name_plural = 'histórico de níveis'
        ordering = ['-criado_em']
        indexes = [models.Index(fields=['area', '-criado_em'], name='historico_area_recente')]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(origem='defesa-civil') | models.Q(responsavel__isnull=False),
                name='historico_defesa_civil_tem_responsavel',
            ),
            models.CheckConstraint(
                condition=~models.Q(nivel_novo='perigo') | models.Q(origem='defesa-civil'),
                name='historico_perigo_so_defesa_civil',
            ),
        ]

    def __str__(self):
        return f'{self.area}: {self.nivel_anterior} → {self.nivel_novo}'
