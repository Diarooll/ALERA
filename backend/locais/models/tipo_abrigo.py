from django.db import models


class TipoAbrigo(models.Model):
    """O que é o abrigo (escola, igreja...). O admin pode criar tipos novos."""

    nome = models.CharField(max_length=60, unique=True)
    icone = models.CharField('ícone', max_length=8, blank=True, default='📍')

    class Meta:
        verbose_name = 'tipo de abrigo'
        verbose_name_plural = 'tipos de abrigo'
        ordering = ['nome']

    def __str__(self):
        return self.nome
