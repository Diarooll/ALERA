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
