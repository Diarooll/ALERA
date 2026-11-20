from django.conf import settings
from django.db import models

from locais.models import AreaRisco, Nivel


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
    # Orientação escrita pela Defesa Civil no alerta (a previsão não escreve)
    mensagem = models.CharField(max_length=300, blank=True)
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
