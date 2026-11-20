from django.db import models

from .area_risco import AreaRisco

RAIO_MINIMO_M = 50
RAIO_MAXIMO_M = 3000


class CirculoRisco(models.Model):
    """Uma bolinha no mapa. Várias bolinhas juntas desenham o formato da área de risco."""

    area = models.ForeignKey(
        AreaRisco, on_delete=models.CASCADE, related_name='circulos', verbose_name='área de risco'
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    raio_m = models.PositiveIntegerField('raio em metros')

    class Meta:
        verbose_name = 'bolinha de risco'
        verbose_name_plural = 'bolinhas de risco'
        ordering = ['id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(raio_m__gte=RAIO_MINIMO_M, raio_m__lte=RAIO_MAXIMO_M),
                name='circulo_raio_valido',
            ),
        ]

    def __str__(self):
        return f'{self.area}: {self.raio_m} m'
