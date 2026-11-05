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


class Abrigo(models.Model):
    class Situacao(models.TextChoices):
        ABERTO = 'aberto', 'Aberto'
        POUCAS_VAGAS = 'poucas', 'Poucas vagas'
        SO_ALERTA = 'so-alerta', 'Só em nível de alerta'
        FECHADO = 'fechado', 'Fechado'

    nome = models.CharField(max_length=150)
    tipo = models.ForeignKey(
        TipoAbrigo, on_delete=models.PROTECT, null=True, blank=True, related_name='abrigos'
    )
    referencia = models.CharField('referência', max_length=150, blank=True)
    # O abrigo não pertence mais a uma área: o morador escolhe o que fica mais perto
    area = models.ForeignKey(
        AreaRisco,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='abrigos',
        verbose_name='área de risco',
    )
    situacao = models.CharField(
        'situação', max_length=10, choices=Situacao.choices, default=Situacao.ABERTO
    )
    # Posição no mapa: o admin clica no mapa do painel. Latitude e longitude andam juntas
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    capacidade = models.PositiveIntegerField('capacidade (vagas)', null=True, blank=True)
    # Antigos, digitados à mão. Agora a distância é calculada para cada morador (locais.servicos)
    distancia_m = models.PositiveIntegerField('distância em metros', null=True, blank=True)
    tempo_a_pe_min = models.PositiveIntegerField('minutos a pé', null=True, blank=True)
    passos_rota = models.TextField('passos da rota', blank=True, help_text='Um passo por linha.')
    rua_a_evitar = models.CharField('rua a evitar', max_length=150, blank=True)
    desenho_mapa = models.TextField('desenho do mapa', blank=True)

    class Meta:
        ordering = ['nome']
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(latitude__isnull=True, longitude__isnull=True)
                    | models.Q(latitude__isnull=False, longitude__isnull=False)
                ),
                name='abrigo_lat_lng_juntas',
            ),
        ]

    def __str__(self):
        return self.nome
