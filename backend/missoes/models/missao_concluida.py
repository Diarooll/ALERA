from django.conf import settings
from django.db import models

from .missao import Missao


class MissaoConcluida(models.Model):
    # Ao excluir a conta, os pontos da pessoa também saem do ranking
    morador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='missoes_concluidas'
    )
    missao = models.ForeignKey(
        Missao, on_delete=models.PROTECT, related_name='conclusoes', verbose_name='missão'
    )
    # Guarda os pontos da época: editar a missão depois não muda o que já foi ganho
    pontos = models.PositiveIntegerField()
    concluida_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'missão concluída'
        verbose_name_plural = 'missões concluídas'
        ordering = ['-concluida_em']
        constraints = [
            models.UniqueConstraint(fields=['morador', 'missao'], name='missao_uma_vez_por_morador'),
        ]

    def __str__(self):
        return f'{self.morador}: {self.missao}'
