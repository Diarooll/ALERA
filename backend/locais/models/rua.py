from django.db import models

from .area_risco import AreaRisco


class Rua(models.Model):
    nome = models.CharField(max_length=150)
    bairro = models.CharField(max_length=120)
    area = models.ForeignKey(
        AreaRisco, on_delete=models.PROTECT, related_name='ruas', verbose_name='área de risco'
    )

    class Meta:
        ordering = ['bairro', 'nome']
        constraints = [
            models.UniqueConstraint(fields=['nome', 'bairro'], name='rua_unica_no_bairro'),
        ]

    def __str__(self):
        return f'{self.nome}, {self.bairro}'
