from django.db import models


class Missao(models.Model):
    codigo = models.SlugField('código', unique=True)
    titulo = models.CharField('título', max_length=80)
    descricao = models.TextField('descrição')
    pontos = models.PositiveIntegerField()
    ordem = models.PositiveSmallIntegerField(default=0)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'missão'
        verbose_name_plural = 'missões'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.titulo
