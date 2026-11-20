from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from usuarios.models import Usuario

from ..models import Abrigo, AreaRisco, Rua


class LocaisTestes(TestCase):
    def setUp(self):
        self.area = AreaRisco.objects.create(nome='Área Exemplo')
        self.rua = Rua.objects.create(nome='Rua Exemplo', bairro='Centro', area=self.area)
        self.abrigo = Abrigo.objects.create(
            nome='Escola Exemplo', area=self.area, distancia_m=600, tempo_a_pe_min=8
        )

    def test_area_comeca_em_normal(self):
        self.assertEqual(self.area.nivel, 'normal')

    def test_nivel_invalido_e_recusado_pelo_banco(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AreaRisco.objects.filter(pk=self.area.pk).update(nivel='inventado')

    def test_nao_repete_rua_no_mesmo_bairro(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rua.objects.create(nome='Rua Exemplo', bairro='Centro', area=self.area)
        Rua.objects.create(nome='Rua Exemplo', bairro='São Mateus', area=self.area)

    def test_area_com_rua_nao_pode_ser_apagada(self):
        with self.assertRaises(ProtectedError):
            self.area.delete()

    def test_rua_com_morador_nao_pode_ser_apagada(self):
        Usuario.objects.create_user('morador@exemplo.com', 'senha-do-app-1', rua=self.rua)
        with self.assertRaises(ProtectedError):
            self.rua.delete()

    def test_apagar_abrigo_so_limpa_o_abrigo_salvo(self):
        morador = Usuario.objects.create_user(
            'morador@exemplo.com', 'senha-do-app-1', abrigo=self.abrigo
        )
        self.abrigo.delete()
        morador.refresh_from_db()
        self.assertIsNone(morador.abrigo)
