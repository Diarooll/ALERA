from django.db import models
from django.utils import timezone


class Nivel(models.TextChoices):
    NORMAL = 'normal', 'Normal'
    ATENCAO = 'atencao', 'Atenção'
    ALERTA = 'alerta', 'Alerta'
    PERIGO = 'perigo', 'Perigo'


class AreaRisco(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    # Só muda por alertas.servicos.mudar_nivel, que também grava o histórico
    nivel = models.CharField('nível', max_length=10, choices=Nivel.choices, default=Nivel.NORMAL)
    nivel_atualizado_em = models.DateTimeField('nível atualizado em', default=timezone.now)

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


class Abrigo(models.Model):
    class Situacao(models.TextChoices):
        ABERTO = 'aberto', 'Aberto'
        POUCAS_VAGAS = 'poucas', 'Poucas vagas'
        SO_ALERTA = 'so-alerta', 'Só em nível de alerta'
        FECHADO = 'fechado', 'Fechado'

    nome = models.CharField(max_length=150)
    referencia = models.CharField('referência', max_length=150, blank=True)
    area = models.ForeignKey(
        AreaRisco, on_delete=models.PROTECT, related_name='abrigos', verbose_name='área de risco'
    )
    situacao = models.CharField(
        'situação', max_length=10, choices=Situacao.choices, default=Situacao.ABERTO
    )
    # Na demo, distância, tempo, rota e mapa são cadastrados à mão: nada é calculado
    distancia_m = models.PositiveIntegerField('distância em metros')
    tempo_a_pe_min = models.PositiveIntegerField('minutos a pé')
    passos_rota = models.TextField('passos da rota', blank=True, help_text='Um passo por linha.')
    rua_a_evitar = models.CharField('rua a evitar', max_length=150, blank=True)
    desenho_mapa = models.TextField('desenho do mapa', blank=True)

    class Meta:
        ordering = ['distancia_m', 'nome']

    def __str__(self):
        return self.nome
