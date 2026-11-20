from django.db import models

from .area_risco import AreaRisco


class Bairro(models.Model):
    """Liga o bairro do morador (vindo do CEP) à área de risco que o atende."""

    nome = models.CharField(max_length=120)
    cidade = models.CharField(max_length=120)
    # Bairro novo nasce sem área: o morador vê nível Normal até o admin completar
    area = models.ForeignKey(
        AreaRisco,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bairros',
        verbose_name='área de risco',
    )

    class Meta:
        ordering = ['cidade', 'nome']
        constraints = [
            models.UniqueConstraint(fields=['nome', 'cidade'], name='bairro_unico_na_cidade'),
        ]

    def __str__(self):
        return f'{self.nome}, {self.cidade}'
