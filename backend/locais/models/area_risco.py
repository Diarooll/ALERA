from django.db import models
from django.utils import timezone

from .nivel import Nivel


class AreaRisco(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    # Só muda por alertas.servicos.mudar_nivel, que também grava o histórico
    nivel = models.CharField('nível', max_length=10, choices=Nivel.choices, default=Nivel.NORMAL)
    nivel_atualizado_em = models.DateTimeField('nível atualizado em', default=timezone.now)
    # O que a Defesa Civil escreveu no último alerta. O app junta com o abrigo do morador
    orientacao = models.CharField('orientação', max_length=300, blank=True)

    class Meta:
        verbose_name = 'área de risco'
        verbose_name_plural = 'áreas de risco'
        ordering = ['nome']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nivel__in=Nivel.values), name='area_nivel_valido'
            ),
        ]

    def __str__(self):
        return self.nome
