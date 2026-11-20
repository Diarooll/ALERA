from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from rest_framework.test import APITestCase
CADASTRO = '/api/auth/cadastro/'
LOGIN = '/api/auth/login/'
ME = '/api/me/'
DADOS = {
    'email': 'Maria@Exemplo.com',
    'senha': 'chuva-forte-2026',
    'telefone': '(32) 99999-0000',
    'cep': '36010-000',
    'logradouro': 'Rua Tal',
    'numero': '10',
    'bairro': 'Centro',
    'cidade': 'Juiz de Fora',
    'consentimento': True,
}


class Base(APITestCase):
    def setUp(self):
        cache.clear()  # zera o limite de tentativas entre os testes
        # Nunca consulta o OpenStreetMap de verdade nos testes
        patcher = patch(
            'usuarios.servicos.localizar',
            return_value=(Decimal('-21.764200'), Decimal('-43.350300')),
        )
        self.localizar = patcher.start()
        self.addCleanup(patcher.stop)
