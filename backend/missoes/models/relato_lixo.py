from django.conf import settings
from django.db import models


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
