import http.client
import json
import time
import urllib.parse
import urllib.request
from decimal import Decimal

URL = 'https://nominatim.openstreetmap.org/search'
# O Nominatim exige que o app se identifique. Sem dado pessoal nenhum.
CABECALHO = {'User-Agent': 'ALERA-demo/1.0 (projeto de faculdade)'}
SEM_NUMERO = {'', 's/n', 'sn', 'sem numero', 'sem número'}
# O serviço aceita no máximo 1 consulta por segundo
PAUSA_S = 1


class ServicoFora(Exception):
    """O Nominatim falhou: sem internet, fora do ar ou resposta quebrada.

    Não adianta tentar as outras buscas agora; cada uma esperaria o tempo limite de novo.
    """


def _buscar(parametros):
    """Uma consulta ao Nominatim. Devolve o primeiro lugar achado ou None se não achou nada."""
    consulta = urllib.parse.urlencode(
        {**parametros, 'format': 'json', 'limit': 1, 'countrycodes': 'br', 'addressdetails': 1}
    )
    pedido = urllib.request.Request(f'{URL}?{consulta}', headers=CABECALHO)
    try:
        with urllib.request.urlopen(pedido, timeout=5) as resposta:
            achados = json.load(resposta)
    except (OSError, ValueError, http.client.HTTPException) as erro:
        raise ServicoFora from erro

    # O esperado é uma lista de lugares. Qualquer outra coisa conta como "não achou"
    if isinstance(achados, list) and achados and isinstance(achados[0], dict):
        return achados[0]
    return None


def _posicao(achado):
    try:
        return (
            Decimal(achado['lat']).quantize(Decimal('0.000001')),
            Decimal(achado['lon']).quantize(Decimal('0.000001')),
        )
    except (KeyError, TypeError, ArithmeticError):
        return None


def _formatar_cep(cep):
    digitos = ''.join(c for c in cep or '' if c.isdigit())
    return f'{digitos[:5]}-{digitos[5:]}' if len(digitos) == 8 else ''


def localizar(logradouro, numero, bairro, cidade, cep=''):
    """Acha latitude e longitude de um endereço no OpenStreetMap.

    Devolve (latitude, longitude) ou None se não achar ou se o serviço falhar.

    1. Rua com número. Se o mapa conhece o número, essa é a posição.
    2. No Brasil muitos números não estão no mapa, e aí ele devolve o meio da rua,
       que numa avenida comprida fica longe da casa. O CEP cobre um trecho curto
       da rua, então vale mais que o meio da rua.
    3. Sem CEP achado, fica o meio da rua; sem nada, a busca em texto livre.
    O morador sempre pode corrigir tocando no mapa em Meus dados.

    Se o serviço falhar em qualquer passo, desiste na hora: o cadastro não fica preso
    esperando três vezes o tempo limite.
    """
    try:
        return _procurar(logradouro, numero, bairro, cidade, cep)
    except ServicoFora:
        return None


def _procurar(logradouro, numero, bairro, cidade, cep):
    rua = logradouro.strip()
    numero = numero.strip()
    tem_numero = numero.lower() not in SEM_NUMERO
    cidade = cidade.strip()

    pela_rua = _buscar({'street': f'{numero} {rua}' if tem_numero else rua, 'city': cidade})
    if pela_rua and tem_numero and pela_rua.get('address', {}).get('house_number'):
        return _posicao(pela_rua)

    cep_formatado = _formatar_cep(cep)
    if cep_formatado:
        time.sleep(PAUSA_S)
        pelo_cep = _buscar({'postalcode': cep_formatado})
        if pelo_cep:
            return _posicao(pelo_cep)

    if pela_rua:
        return _posicao(pela_rua)

    time.sleep(PAUSA_S)
    rua_com_numero = f'{rua}, {numero}' if tem_numero else rua
    texto_livre = _buscar({'q': f'{rua_com_numero}, {bairro}, {cidade}, Brasil'})
    return _posicao(texto_livre) if texto_livre else None
