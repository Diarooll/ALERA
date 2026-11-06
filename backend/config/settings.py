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
    # ALERA
    'usuarios',
    'locais',
    'alertas',
    'missoes',
    'sensores',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
    # Quantos proxies de confiança ficam na frente do servidor. Com 0, o limite conta pelo
    # IP da conexão. Sem isto, o DRF confiava no cabeçalho X-Forwarded-For, que qualquer
    # um escreve, e o limite de tentativas caía trocando o cabeçalho a cada chute
    'NUM_PROXIES': int(os.environ.get('DJANGO_NUM_PROXIES', '0')),
}

SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME': timedelta(hours=2)}

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
