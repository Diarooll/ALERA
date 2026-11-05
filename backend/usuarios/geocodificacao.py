import json
import urllib.parse
import urllib.request
from decimal import Decimal

URL = 'https://nominatim.openstreetmap.org/search'
# O Nominatim exige que o app se identifique. Sem dado pessoal nenhum.
CABECALHO = {'User-Agent': 'ALERA-demo/1.0 (projeto de faculdade)'}
SEM_NUMERO = {'', 's/n', 'sn', 'sem numero', 'sem número'}


def localizar(logradouro, numero, bairro, cidade):
    """Acha latitude e longitude de um endereço no OpenStreetMap.

    Devolve (latitude, longitude) ou None se não achar ou se o serviço falhar.
    Uma consulta por cadastro, bem abaixo do limite de 1 por segundo do serviço.
    """
    rua = logradouro.strip()
    if numero.strip().lower() not in SEM_NUMERO:
        rua = f'{rua}, {numero.strip()}'

    consulta = urllib.parse.urlencode(
        {'q': f'{rua}, {bairro}, {cidade}, Brasil', 'format': 'json', 'limit': 1}
    )
    pedido = urllib.request.Request(f'{URL}?{consulta}', headers=CABECALHO)

    try:
        with urllib.request.urlopen(pedido, timeout=5) as resposta:
            achados = json.load(resposta)
        return Decimal(achados[0]['lat']).quantize(Decimal('0.000001')), Decimal(
            achados[0]['lon']
        ).quantize(Decimal('0.000001'))
    except (OSError, ValueError, KeyError, IndexError, ArithmeticError):
        return None
