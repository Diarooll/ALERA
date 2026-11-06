import math

from .models import AreaRisco, Nivel

RAIO_TERRA_M = 6_371_000
# Passo de quem anda a pé, mais ou menos 4,8 km/h
METROS_POR_MINUTO = 80
# Do menos ao mais grave, para escolher o pior quando a casa está em mais de uma área
GRAVIDADE = {nivel: ordem for ordem, nivel in enumerate(Nivel.values)}


def distancia_em_metros(lat1, lon1, lat2, lon2):
    """Distância em linha reta entre dois pontos (haversine). Não segue as ruas."""
    f1, f2 = math.radians(float(lat1)), math.radians(float(lat2))
    df = f2 - f1
    dl = math.radians(float(lon2) - float(lon1))
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return round(2 * RAIO_TERRA_M * math.asin(math.sqrt(a)))


def tempo_a_pe_min(metros):
    return max(1, math.ceil(metros / METROS_POR_MINUTO))


def areas_do_ponto(latitude, longitude):
    """Áreas de risco com alguma bolinha que contém o ponto, da mais grave para a menos."""
    if latitude is None or longitude is None:
        return []

    areas = [
        area
        for area in AreaRisco.objects.prefetch_related('circulos')
        if any(
            distancia_em_metros(latitude, longitude, c.latitude, c.longitude) <= c.raio_m
            for c in area.circulos.all()
        )
    ]
    return sorted(areas, key=lambda area: (-GRAVIDADE[area.nivel], area.nome))


def area_mais_grave(latitude, longitude):
    areas = areas_do_ponto(latitude, longitude)
    return areas[0] if areas else None
