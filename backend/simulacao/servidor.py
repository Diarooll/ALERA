"""Sobe o servidor do ALERA só para a simulação. Quem chama é o simular.py.

A única diferença para o `manage.py runserver` normal: a busca do endereço no mapa
(Nominatim) fica desligada. Assim a simulação não manda endereço inventado para um
serviço de fora e não depende de internet. O morador simulado marca a casa no mapa
pelo "Meus dados", do mesmo jeito que faz quem não foi achado no cadastro.
"""

import os
import sys
from pathlib import Path

PASTA_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA_BACKEND))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402

from usuarios import geocodificacao  # noqa: E402

# Responde "não achei" sem sair do computador
geocodificacao.localizar = lambda *args, **kwargs: None

porta = sys.argv[1]
call_command('runserver', f'127.0.0.1:{porta}', use_reloader=False)
