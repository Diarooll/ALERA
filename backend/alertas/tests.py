from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from rest_framework.test import APIClient

from locais.models import AreaRisco, Nivel
from usuarios.models import Usuario

from .models import HistoricoNivel, Previsao
from .servicos import mudar_nivel

DEFESA_CIVIL = HistoricoNivel.Origem.DEFESA_CIVIL
PREVISAO = HistoricoNivel.Origem.PREVISAO


class Base(TestCase):
    def setUp(self):
        self.area = AreaRisco.objects.create(nome='Área Exemplo')
        self.agente = Usuario.objects.create_superuser('agente@exemplo.com', 'senha-do-painel-1')


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


class RegrasDoBancoTestes(Base):
    def test_defesa_civil_exige_responsavel(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            HistoricoNivel.objects.create(
                area=self.area, nivel_anterior='normal', nivel_novo='alerta', origem=DEFESA_CIVIL
            )

    def test_previsao_nao_define_perigo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Previsao.objects.create(
                area=self.area, chuva_mm_24h=90, nivel_calculado=Nivel.PERIGO, fonte='teste'
            )

    def test_chuva_nao_pode_ser_negativa(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Previsao.objects.create(
                area=self.area, chuva_mm_24h=-1, nivel_calculado=Nivel.NORMAL, fonte='teste'
            )


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


class EmitirAlertaTestes(Base):
    def setUp(self):
        super().setUp()
        self.admzinho = Usuario.objects.create_user('defesa@exemplo.com', 'senha-do-painel-1', is_staff=True)
        self.outra = AreaRisco.objects.create(nome='Outra Área')
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.admzinho)

    def emitir(self, areas, nivel='perigo', mensagem='Saia de casa.'):
        return self.cliente.post(
            '/api/alertas/', {'areas': areas, 'nivel': nivel, 'mensagem': mensagem}, format='json'
        )

    def test_emite_para_varias_areas_de_uma_vez(self):
        resposta = self.emitir([self.area.pk, self.outra.pk])
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(len(resposta.data), 2)

        for area in (self.area, self.outra):
            area.refresh_from_db()
            self.assertEqual(area.nivel, Nivel.PERIGO)
            self.assertEqual(area.orientacao, 'Saia de casa.')
        self.assertTrue(all(h.responsavel == self.admzinho for h in HistoricoNivel.objects.all()))

    def test_lista_os_ultimos_alertas(self):
        self.emitir([self.area.pk])
        ultimos = self.cliente.get('/api/alertas/').data
        self.assertEqual(ultimos[0]['area'], 'Área Exemplo')
        self.assertEqual(ultimos[0]['nivel_novo'], 'perigo')
        self.assertEqual(ultimos[0]['mensagem'], 'Saia de casa.')
        self.assertEqual(ultimos[0]['responsavel'], 'defesa@exemplo.com')

    def test_precisa_de_pelo_menos_uma_area(self):
        self.assertEqual(self.emitir([]).status_code, 400)

    def test_morador_nao_emite_nem_ve_alertas(self):
        morador = Usuario.objects.create_user('morador@exemplo.com', 'senha-do-app-1')
        self.cliente.force_authenticate(morador)
        self.assertEqual(self.emitir([self.area.pk]).status_code, 403)
        self.assertEqual(self.cliente.get('/api/alertas/').status_code, 403)
        self.area.refresh_from_db()
        self.assertEqual(self.area.nivel, Nivel.NORMAL)
