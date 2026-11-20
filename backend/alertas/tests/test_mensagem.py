from locais.models import Nivel

from ..servicos import mudar_nivel
from .base import DEFESA_CIVIL, PREVISAO, Base


class MensagemTestes(Base):
    def test_alerta_guarda_a_orientacao_na_area_e_no_historico(self):
        historico = mudar_nivel(self.area, Nivel.PERIGO, DEFESA_CIVIL, self.agente, mensagem=' Saia já. ')
        self.area.refresh_from_db()
        self.assertEqual(self.area.orientacao, 'Saia já.')
        self.assertEqual(historico.mensagem, 'Saia já.')

    def test_mesmo_nivel_com_outra_orientacao_grava(self):
        mudar_nivel(self.area, Nivel.ALERTA, DEFESA_CIVIL, self.agente, mensagem='Primeira')
        self.assertIsNotNone(mudar_nivel(self.area, Nivel.ALERTA, DEFESA_CIVIL, self.agente, mensagem='Segunda'))
        self.area.refresh_from_db()
        self.assertEqual(self.area.orientacao, 'Segunda')

    def test_previsao_no_mesmo_nivel_nao_apaga_a_orientacao(self):
        mudar_nivel(self.area, Nivel.ALERTA, DEFESA_CIVIL, self.agente, mensagem='Fique atento')
        self.assertIsNone(mudar_nivel(self.area, Nivel.ALERTA, PREVISAO))
        self.area.refresh_from_db()
        self.assertEqual(self.area.orientacao, 'Fique atento')

    def test_previsao_que_muda_o_nivel_tira_a_orientacao_antiga(self):
        mudar_nivel(self.area, Nivel.ALERTA, DEFESA_CIVIL, self.agente, mensagem='Fique atento')
        mudar_nivel(self.area, Nivel.ATENCAO, PREVISAO)
        self.area.refresh_from_db()
        self.assertEqual(self.area.orientacao, '')
