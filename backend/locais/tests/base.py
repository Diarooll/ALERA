import math


# Um grau de latitude tem uns 111 km
METROS_POR_GRAU = 111_195
CASA = (-21.7642, -43.3503)


def ao_norte(metros, lat=CASA[0], lng=CASA[1]):
    return round(lat + metros / METROS_POR_GRAU, 6), lng


def a_leste(metros, lat=CASA[0], lng=CASA[1]):
    # Longe do equador o grau de longitude encolhe: em Juiz de Fora tem uns 103 km
    return lat, round(lng + metros / (METROS_POR_GRAU * math.cos(math.radians(lat))), 6)
