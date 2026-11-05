from django.conf import settings
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


class RelatoLixo(models.Model):
    # Ao excluir a conta, o relato fica para a Defesa Civil, sem ligação com a pessoa
    morador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relatos_de_lixo',
    )
    local = models.CharField(max_length=200)
    descricao = models.TextField('descrição')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'relato de lixo'
        verbose_name_plural = 'relatos de lixo'
        ordering = ['-criado_em']

    def __str__(self):
        return self.local
