from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from locais.models import Nivel

from ..models import HistoricoNivel
from ..servicos import mudar_nivel
from .base import DEFESA_CIVIL, PREVISAO, Base


class MudarNivelTestes(Base):
    def test_muda_a_area_e_grava_quem_mudou(self):
        historico = mudar_nivel(self.area, Nivel.PERIGO, DEFESA_CIVIL, self.agente)

        self.area.refresh_from_db()
        self.assertEqual(self.area.nivel, Nivel.PERIGO)
        self.assertEqual(historico.nivel_anterior, Nivel.NORMAL)
        self.assertEqual(historico.nivel_novo, Nivel.PERIGO)
        self.assertEqual(historico.responsavel, self.agente)

    def test_mesmo_nivel_nao_gera_historico(self):
        self.assertIsNone(mudar_nivel(self.area, Nivel.NORMAL, PREVISAO))
        self.assertFalse(HistoricoNivel.objects.exists())

    def test_falha_no_historico_nao_muda_a_area(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            mudar_nivel(self.area, Nivel.PERIGO, PREVISAO)

        self.area.refresh_from_db()
        self.assertEqual(self.area.nivel, Nivel.NORMAL)

    def test_conta_com_historico_nao_pode_ser_apagada(self):
        mudar_nivel(self.area, Nivel.ALERTA, DEFESA_CIVIL, self.agente)
        with self.assertRaises(ProtectedError):
            self.agente.delete()
