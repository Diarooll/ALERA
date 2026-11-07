import math

from .models import RAIO_MAXIMO_M, CirculoRisco, Nivel

RAIO_TERRA_M = 6_371_000
# Passo de quem anda a pé, mais ou menos 4,8 km/h
METROS_POR_MINUTO = 80
# Do menos ao mais grave, para escolher o pior quando a casa está em mais de uma área
GRAVIDADE = {nivel: ordem for ordem, nivel in enumerate(Nivel.values)}
# O maior raio possível, com 1 m a mais porque a distância é arredondada para o metro
ALCANCE_MAXIMO_M = RAIO_MAXIMO_M + 1


def distancia_em_metros(lat1, lon1, lat2, lon2):
    """Distância em linha reta entre dois pontos (haversine). Não segue as ruas."""
    f1, f2 = math.radians(float(lat1)), math.radians(float(lat2))
    df = f2 - f1
    dl = math.radians(float(lon2) - float(lon1))
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return round(2 * RAIO_TERRA_M * math.asin(math.sqrt(a)))


def tempo_a_pe_min(metros):
    return max(1, math.ceil(metros / METROS_POR_MINUTO))


def area_mais_grave(latitude, longitude):
    """Entre as áreas com alguma bolinha que contém o ponto, a de nível mais grave.

    Empate no nível: vale a primeira em ordem alfabética. Sem área nenhuma, None.
    """
    if latitude is None or longitude is None:
        return None

    # O app pergunta a cada minuto: o banco já separa só as bolinhas que podem alcançar
    # a casa, e a conta exata fica para essas poucas (uma consulta só)
    perto = bolinhas_que_podem_alcancar(float(latitude), float(longitude)).select_related('area')
    areas = {
        c.area
        for c in perto
        if distancia_em_metros(latitude, longitude, c.latitude, c.longitude) <= c.raio_m
    }
    return min(areas, key=lambda area: (-GRAVIDADE[area.nivel], area.nome), default=None)


def bolinhas_que_podem_alcancar(lat, lng):
    """Bolinhas com o centro num retângulo em volta do ponto, do tamanho do maior raio.

    É só um filtro grosso: quem decide se a casa está dentro é distancia_em_metros.
    """
    angulo = ALCANCE_MAXIMO_M / RAIO_TERRA_M
    folga_lat = math.degrees(angulo)
    bolinhas = CirculoRisco.objects.filter(latitude__range=(lat - folga_lat, lat + folga_lat))

    # Perto do polo o grau de longitude encolhe até sumir, e na linha de data a longitude
    # dá a volta (180 vira -180). Nesses casos fica só o filtro de latitude
    encolhe = math.cos(math.radians(lat))
    if encolhe > math.sin(angulo):
        folga_lng = math.degrees(math.asin(math.sin(angulo) / encolhe))
        if -180 <= lng - folga_lng and lng + folga_lng <= 180:
            bolinhas = bolinhas.filter(longitude__range=(lng - folga_lng, lng + folga_lng))
    return bolinhas
