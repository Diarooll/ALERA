from django.db import models


class Nivel(models.TextChoices):
    NORMAL = 'normal', 'Normal'
    ATENCAO = 'atencao', 'Atenção'
    ALERTA = 'alerta', 'Alerta'
    PERIGO = 'perigo', 'Perigo'
