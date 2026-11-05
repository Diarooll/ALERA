from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

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


class AdminDoDjangoTestes(Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.agente)
        self.url = f'/admin/locais/arearisco/{self.area.pk}/change/'

    def salvar(self, nivel):
        return self.client.post(self.url, {'nome': self.area.nome, 'nivel': nivel})

    def test_adm_principal_nao_muda_o_nivel(self):
        self.assertEqual(self.salvar('perigo').status_code, 302)

        self.area.refresh_from_db()
        self.assertEqual(self.area.nivel, Nivel.NORMAL)
        self.assertFalse(HistoricoNivel.objects.exists())

    def test_adm_principal_muda_o_nome_da_area(self):
        self.client.post(self.url, {'nome': 'Área Nova'})
        self.area.refresh_from_db()
        self.assertEqual(self.area.nome, 'Área Nova')

    def test_morador_nao_entra_no_painel(self):
        self.client.force_login(Usuario.objects.create_user('morador@exemplo.com', 'senha-do-app-1'))
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.salvar('perigo')
        self.area.refresh_from_db()
        self.assertEqual(self.area.nivel, Nivel.NORMAL)
