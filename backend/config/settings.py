"""Configurações do back-end do ALERA.

Os valores que mudam entre ambientes vêm de variáveis de ambiente, lidas também
de `backend/.env` no desenvolvimento. As variáveis estão listadas em `backend/README.md`.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from django.utils.csp import CSP
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def lista_do_ambiente(nome):
    return [item.strip() for item in os.environ.get(nome, '').split(',') if item.strip()]


def chave_local_de_desenvolvimento():
    """Chave aleatória deste computador, guardada em backend/.chave-local (fora do Git).

    A chave assina os logins. Ela não pode ficar escrita no código: quem lesse o
    repositório conseguiria fabricar o login de qualquer conta, até a do ADM principal.
    Cada computador cria a sua na primeira vez que o servidor sobe.
    """
    arquivo = BASE_DIR / '.chave-local'
    if arquivo.exists():
        chave = arquivo.read_text(encoding='utf-8').strip()
        if chave:
            return chave
    chave = get_random_secret_key()
    try:
        # 'x' não sobrescreve: se o servidor subir dois processos juntos, vale a primeira
        with open(arquivo, 'x', encoding='utf-8') as saida:
            saida.write(chave)
    except FileExistsError:
        return arquivo.read_text(encoding='utf-8').strip() or chave
    return chave


# Fica desligado por padrão: quem desenvolve liga no próprio .env
DEBUG = os.environ.get('DJANGO_DEBUG', '').lower() == 'true'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('Defina DJANGO_SECRET_KEY quando DJANGO_DEBUG não for true.')
    SECRET_KEY = chave_local_de_desenvolvimento()

ALLOWED_HOSTS = lista_do_ambiente('DJANGO_ALLOWED_HOSTS')


INSTALLED_APPS = [
    'config.apps.AleraAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceiros
    'corsheaders',
    'rest_framework',
    # Guarda os tokens de renovação já usados ou encerrados, para não valerem de novo
    'rest_framework_simplejwt.token_blacklist',
    # ALERA
    'usuarios',
    'locais',
    'alertas',
    'missoes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Serve o CSS e o JS do /admin/ quando o servidor é o uvicorn (ele não serve arquivos estáticos)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # Política de conteúdo (CSP): veja o bloco "Segurança" no fim deste arquivo
    'django.middleware.csp.ContentSecurityPolicyMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    # IP de quem acessa e limite de tamanho do pedido. Ficam depois do CORS para a
    # recusa (413) também levar os cabeçalhos dele
    'config.middleware.IpDoVisitante',
    'config.middleware.LimiteDoCorpo',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Entrega às páginas do /admin/ o número de uso único (nonce) da CSP
                'django.template.context_processors.csp',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Banco: PostgreSQL via DATABASE_URL. Sem ela, o SQLite só é aceito em desenvolvimento.
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not DATABASE_URL and not DEBUG:
    raise ImproperlyConfigured('Defina DATABASE_URL quando DJANGO_DEBUG não for true.')

DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}


AUTH_USER_MODEL = 'usuarios.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
# Para onde o collectstatic copia os arquivos. Em desenvolvimento não precisa rodar
STATIC_ROOT = BASE_DIR / 'staticfiles'


# API: toda rota exige login, a menos que libere explicitamente
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    # Limita quem tenta adivinhar senhas, cria contas em massa ou muda o perfil sem parar
    # (cada mudança de endereço consulta o serviço de mapas)
    'DEFAULT_THROTTLE_RATES': {'login': '10/min', 'cadastro': '20/hour', 'perfil': '30/hour'},
    # O limite conta pelo REMOTE_ADDR, que config.middleware.IpDoVisitante já trocou pelo IP
    # de quem acessa (com proxy e Cloudflare, veja o bloco "Segurança"). Com 0, o DRF não lê
    # o X-Forwarded-For, que qualquer um escreve: senão o limite caía trocando o cabeçalho
    'NUM_PROXIES': 0,
}

# Sessão longa sem token longo: o de acesso vence em 20 minutos e o app troca sozinho
# pelo de renovação (30 dias). Cada troca gera um de renovação novo, com mais 30 dias,
# e põe o antigo na lista negra: quem usa o app não cai, e um token vazado logo para de valer
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=20),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    # Trocou a senha, as sessões abertas antes deixam de valer (o token leva uma marca da senha)
    'CHECK_REVOKE_TOKEN': True,
}

# Endereços do front-end que podem chamar a API
CORS_ALLOWED_ORIGINS = lista_do_ambiente('CORS_ALLOWED_ORIGINS')
if DEBUG and not CORS_ALLOWED_ORIGINS:
    # "null" é a origem de uma página aberta direto pelo arquivo, como o README orienta.
    # 5500 é o Live Server do VS Code; 5520 é o front-end aberto pelo .claude/launch.json
    CORS_ALLOWED_ORIGINS = [
        'null',
        'http://127.0.0.1:5500',
        'http://localhost:5500',
        'http://127.0.0.1:5520',
        'http://localhost:5520',
    ]


# Segurança
# Os cabeçalhos e cookies ficam no próprio Django, e não só na Cloudflare, para continuarem
# valendo mesmo se alguém chegar ao servidor sem passar por ela.

# Quem fica na frente do servidor. config.middleware.IpDoVisitante usa isto para achar o IP
# de quem acessa, e o limite de tentativas conta por esse IP. Explicação completa lá
ALERA_NUM_PROXIES = int(os.environ.get('DJANGO_NUM_PROXIES', '0'))
if ALERA_NUM_PROXIES < 0:
    raise ImproperlyConfigured('DJANGO_NUM_PROXIES não pode ser negativo.')
ALERA_ATRAS_DA_CLOUDFLARE = os.environ.get('DJANGO_ATRAS_DA_CLOUDFLARE', '').lower() == 'true'

# Atrás de proxy, o HTTPS termina nele e o Django recebe HTTP comum; o proxy conta no
# X-Forwarded-Proto se o visitante usou HTTPS. Sem proxy, ninguém é ouvido nesse cabeçalho:
# qualquer um poderia escrever "https" numa conexão sem criptografia
if ALERA_NUM_PROXIES or ALERA_ATRAS_DA_CLOUDFLARE:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Endereços (com https://) de onde o navegador pode mandar formulário com cookie, como o login
# do /admin/. Só é preciso quando o endereço visto no navegador não chega igual ao Django
CSRF_TRUSTED_ORIGINS = lista_do_ambiente('DJANGO_CSRF_TRUSTED_ORIGINS')

# Nenhuma rota recebe arquivo, e o maior JSON do app fica muito abaixo de 1 MB.
# config.middleware.LimiteDoCorpo recusa (413) o pedido que passar disso, antes de ler
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024

# A sessão só serve ao /admin/ (a API usa token): dura 8 horas, o JavaScript da página não lê
# os cookies (HttpOnly) e o navegador não os manda em formulário vindo de outro site (Lax)
SESSION_COOKIE_AGE = 60 * 60 * 8
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Já são o padrão do Django; ficam escritos para ninguém desligar sem perceber
X_FRAME_OPTIONS = 'DENY'  # nenhuma página do ALERA abre dentro de outro site
SECURE_CONTENT_TYPE_NOSNIFF = True  # o navegador não trata um JSON como se fosse página
SECURE_REFERRER_POLICY = 'same-origin'  # o endereço visitado não vaza para outros sites
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'  # site que abriu a aba não mexe nela

# CSP da API. Ela só devolve JSON: não carrega nada, não abre em moldura, não envia
# formulário. O /admin/ tem a política dele, em config/admin_site.py
POLITICA_DA_API = {
    'default-src': [CSP.NONE],
    'base-uri': [CSP.NONE],
    'form-action': [CSP.NONE],
    'frame-ancestors': [CSP.NONE],
}

if not DEBUG:
    # Só fora do desenvolvimento, que roda em http://127.0.0.1, sem HTTPS.
    # false só para testar o modo de produção na própria máquina
    SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', '').lower() != 'false'
    # O teste de saúde da hospedagem costuma chamar por HTTP, por dentro
    SECURE_REDIRECT_EXEMPT = [r'^api/saude/$']
    # HSTS: por um ano o navegador só abre o site (e os subdomínios) por HTTPS
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # No desenvolvimento a CSP esconderia o estilo da página amarela de erro do Django
    SECURE_CSP = POLITICA_DA_API

# O "preload" põe o domínio numa lista gravada nos navegadores, difícil de desfazer.
# Só vale para o domínio principal e feito de propósito, então este aviso fica calado
SILENCED_SYSTEM_CHECKS = ['security.W021']
