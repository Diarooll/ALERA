from unittest.mock import patch

from rest_framework.test import APIClient

from locais.models import AreaRisco, Nivel
from usuarios.models import Usuario

from ..models import HistoricoNivel
from ..servicos import mudar_nivel
from .base import Base


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

    def test_nivel_desconhecido_e_recusado(self):
        resposta = self.emitir([self.area.pk], nivel='inventado')
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('nivel', resposta.data)
        self.assertFalse(HistoricoNivel.objects.exists())

    def test_area_que_nao_existe_recusa_o_alerta_inteiro(self):
        resposta = self.emitir([self.area.pk, 999_999])
        self.assertEqual(resposta.status_code, 400)
        self.area.refresh_from_db()
        self.assertEqual(self.area.nivel, Nivel.NORMAL)

    def test_area_repetida_no_pedido_grava_uma_vez(self):
        resposta = self.emitir([self.area.pk, self.area.pk])
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(len(resposta.data), 1)
        self.assertEqual(HistoricoNivel.objects.count(), 1)

    def test_orientacao_maior_que_o_limite_e_recusada(self):
        self.assertEqual(self.emitir([self.area.pk], mensagem='x' * 301).status_code, 400)
        self.assertFalse(HistoricoNivel.objects.exists())

    def test_erro_numa_area_nao_deixa_alerta_pela_metade(self):
        chamadas = []

        def falha_na_segunda(*args, **kwargs):
            chamadas.append(args[0])
            if len(chamadas) == 2:
                raise RuntimeError('falha no meio do alerta')
            return mudar_nivel(*args, **kwargs)

        with patch('alertas.views.mudar_nivel', side_effect=falha_na_segunda):
            with self.assertRaises(RuntimeError):
                self.emitir([self.area.pk, self.outra.pk])

        # A primeira área tinha mudado antes da falha: tem que voltar como estava
        self.area.refresh_from_db()
        self.assertEqual(self.area.nivel, Nivel.NORMAL)
        self.assertFalse(HistoricoNivel.objects.exists())

    def test_morador_nao_emite_nem_ve_alertas(self):
        morador = Usuario.objects.create_user('morador@exemplo.com', 'senha-do-app-1')
        self.cliente.force_authenticate(morador)
        self.assertEqual(self.emitir([self.area.pk]).status_code, 403)
        self.assertEqual(self.cliente.get('/api/alertas/').status_code, 403)
        self.area.refresh_from_db()
        self.assertEqual(self.area.nivel, Nivel.NORMAL)
