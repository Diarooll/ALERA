"""Middlewares de segurança do ALERA. As variáveis que os ligam ficam no bloco
"Segurança" do settings.py e estão explicadas no backend/README.md."""

import ipaddress

from django.conf import settings
from django.http import JsonResponse

# Faixas de onde a Cloudflare se conecta ao nosso servidor.
# Fonte: https://www.cloudflare.com/ips/ (conferida em novembro de 2026).
# Se a Cloudflare criar uma faixa nova e ela faltar aqui, nada fica aberto: quem chegar
# por ela só passa a ser contado pelo IP da Cloudflare, e não pelo do visitante
FAIXAS_DA_CLOUDFLARE = tuple(
    ipaddress.ip_network(faixa)
    for faixa in (
        '173.245.48.0/20',
        '103.21.244.0/22',
        '103.22.200.0/22',
        '103.31.4.0/22',
        '141.101.64.0/18',
        '108.162.192.0/18',
        '190.93.240.0/20',
        '188.114.96.0/20',
        '197.234.240.0/22',
        '198.41.128.0/17',
        '162.158.0.0/15',
        '104.16.0.0/13',
        '104.24.0.0/14',
        '172.64.0.0/13',
        '131.0.72.0/22',
        '2400:cb00::/32',
        '2606:4700::/32',
        '2803:f800::/32',
        '2405:b500::/32',
        '2405:8100::/32',
        '2a06:98c0::/29',
        '2c0f:f248::/32',
    )
)


def ler_ip(texto):
    """O IP escrito no texto, ou None se não for um IP."""
    try:
        ip = ipaddress.ip_address((texto or '').strip())
    except ValueError:
        return None
    # "::ffff:1.2.3.4" é o 1.2.3.4 visto por um servidor que fala IPv6: conta como o mesmo
    if ip.version == 6 and ip.ipv4_mapped:
        return ip.ipv4_mapped
    return ip


def veio_da_cloudflare(ip):
    return any(ip in faixa for faixa in FAIXAS_DA_CLOUDFLARE)


def ip_do_visitante(meta):
    """Descobre o IP de quem fez o pedido sem acreditar em cabeçalho que o próprio visitante escreve."""
    ip = ler_ip(meta.get('REMOTE_ADDR'))
    if ip is None:
        return None

    # 1. Proxies de confiança (DJANGO_NUM_PROXIES). Cada proxy acrescenta, no FIM do
    #    X-Forwarded-For, o IP de quem se conectou a ele. O visitante consegue escrever o
    #    começo da lista, mas não o fim. Por isso vale a posição N contada do fim: ela foi
    #    escrita pelo nosso proxy mais de fora. É a mesma conta que o DRF fazia
    num_proxies = settings.ALERA_NUM_PROXIES
    encaminhado = meta.get('HTTP_X_FORWARDED_FOR')
    if num_proxies and encaminhado:
        partes = encaminhado.split(',')
        # Se ali não houver um IP, o valor veio do visitante (proxy mal configurado).
        # Fica o IP do proxy: pior todos dividirem um limite do que alguém ganhar limite infinito
        ip = ler_ip(partes[-min(num_proxies, len(partes))]) or ip

    # 2. Cloudflare (DJANGO_ATRAS_DA_CLOUDFLARE). Ela manda o IP do visitante no cabeçalho
    #    CF-Connecting-IP. Só que quem chega ao servidor direto, sem passar pela Cloudflare,
    #    também pode escrever esse cabeçalho e trocar de "IP" a cada tentativa. Então ele
    #    só vale quando quem entregou o pedido (o IP do passo 1) é mesmo da Cloudflare
    if settings.ALERA_ATRAS_DA_CLOUDFLARE and veio_da_cloudflare(ip):
        ip = ler_ip(meta.get('HTTP_CF_CONNECTING_IP')) or ip

    # 3. Quem usa IPv6 costuma receber um bloco inteiro (/64) só para si, com bilhões de
    #    endereços. Se cada endereço contasse à parte, bastava trocar a cada tentativa para
    #    escapar do limite. Então o bloco todo conta como um IP só
    if ip.version == 6:
        ip = ipaddress.ip_network(f'{ip}/64', strict=False).network_address
    return str(ip)


class IpDoVisitante:
    """Troca o REMOTE_ADDR pelo IP de quem acessa, antes de qualquer limite de tentativas.

    Os limites da API (DRF) e o do login do /admin/ contam pelo REMOTE_ADDR. Descobrir o IP
    aqui, num lugar só, faz todos contarem a mesma pessoa do mesmo jeito.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = ip_do_visitante(request.META)
        if ip:
            request.META['REMOTE_ADDR'] = ip
        return self.get_response(request)


class LimiteDoCorpo:
    """Recusa, antes de ler, o pedido com corpo maior que DATA_UPLOAD_MAX_MEMORY_SIZE.

    O Django sozinho já barra JSON e formulário grandes, mas deixa passar arquivo enviado
    (multipart), que vai para o disco. Nenhuma rota do ALERA recebe arquivo, então o pedido
    inteiro precisa caber no limite. Pedido sem Content-Length chega ao Django sem corpo.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            tamanho = int(request.META.get('CONTENT_LENGTH') or 0)
        except ValueError:
            tamanho = 0
        limite = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
        if limite is not None and tamanho > limite:
            return JsonResponse({'detail': 'O pedido é grande demais.'}, status=413)
        return self.get_response(request)
