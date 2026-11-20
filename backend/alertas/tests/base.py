from django.test import TestCase

from locais.models import AreaRisco
from usuarios.models import Usuario

from ..models import HistoricoNivel
DEFESA_CIVIL = HistoricoNivel.Origem.DEFESA_CIVIL
PREVISAO = HistoricoNivel.Origem.PREVISAO


class Base(TestCase):
    def setUp(self):
        self.area = AreaRisco.objects.create(nome='Área Exemplo')
        self.agente = Usuario.objects.create_superuser('agente@exemplo.com', 'senha-do-painel-1')
