import importlib.util
import os
import re
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.management.utils import get_random_secret_key
LOGIN = '/api/auth/login/'
CLOUDFLARE = '173.245.48.10'  # um IP de dentro das faixas da Cloudflare
CLOUDFLARE_2 = '162.158.1.2'  # outro, como se fosse outro servidor dela


def settings_de_producao(**ambiente):
    """Lê o settings.py de novo, à parte, como se estivesse em produção (variáveis falsas).

    O settings de verdade já foi lido com as variáveis desta máquina. Assim dá para conferir
    o modo de produção sem mexer nele nem em nenhum .env.
    """
    variaveis = {
        'DJANGO_DEBUG': 'false',
        'DJANGO_SECRET_KEY': get_random_secret_key(),
        'DATABASE_URL': 'sqlite:///producao-de-teste.sqlite3',
        'DJANGO_ALLOWED_HOSTS': 'alera.exemplo',
        'DJANGO_NUM_PROXIES': '0',
        'DJANGO_ATRAS_DA_CLOUDFLARE': 'false',
        'DJANGO_SECURE_SSL_REDIRECT': 'true',
        **ambiente,
    }
    arquivo = Path(settings.BASE_DIR) / 'config' / 'settings.py'
    spec = importlib.util.spec_from_file_location('settings_de_producao', arquivo)
    modulo = importlib.util.module_from_spec(spec)
    with mock.patch.dict(os.environ, variaveis):
        spec.loader.exec_module(modulo)
    return modulo


# O que muda entre desenvolvimento e produção, para repetir nos testes de resposta
NOMES_DE_PRODUCAO = [
    'SECURE_SSL_REDIRECT',
    'SECURE_REDIRECT_EXEMPT',
    'SECURE_HSTS_SECONDS',
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    'SESSION_COOKIE_SECURE',
    'CSRF_COOKIE_SECURE',
    'SECURE_CSP',
    'SECURE_PROXY_SSL_HEADER',
]


def como_em_producao(**ambiente):
    producao = settings_de_producao(**ambiente)
    return {nome: getattr(producao, nome, None) for nome in NOMES_DE_PRODUCAO}


def trechos_que_a_csp_bloquearia(html, nonce):
    """Procura no HTML o que a CSP do /admin/ barraria e quebraria a página."""
    bloqueados = []
    marca = f'nonce="{nonce}"' if nonce else None
    for atributos in re.findall(r'<script\b([^>]*)>', html):
        de_arquivo = re.search(r'\bsrc="/', atributos)
        so_dados = 'type="application/json"' in atributos  # dados, o navegador não executa
        if not (de_arquivo or so_dados or (marca and marca in atributos)):
            bloqueados.append(f'<script{atributos}>')
    for atributos in re.findall(r'<style\b([^>]*)>', html):
        if not (marca and marca in atributos):
            bloqueados.append(f'<style{atributos}>')
    bloqueados += re.findall(r'<[^>]*\sstyle="[^>]*>', html)
    bloqueados += re.findall(r'<[^>]*\son[a-z]+="[^>]*>', html)
    bloqueados += re.findall(r'<link\b[^>]*\bhref="(?!/)[^"]*"[^>]*>', html)
    return bloqueados
