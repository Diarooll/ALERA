from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from usuarios.models import Usuario

from ..models import Missao, MissaoConcluida, RelatoLixo


class MissoesTestes(TestCase):
    def setUp(self):
        self.morador = Usuario.objects.create_user('morador@exemplo.com', 'senha-do-app-1')
        self.missao = Missao.objects.get(codigo='salve-abrigo')

    def concluir(self):
        return MissaoConcluida.objects.create(
            morador=self.morador, missao=self.missao, pontos=self.missao.pontos
        )

    def test_banco_ja_nasce_com_as_quatro_missoes(self):
        pontos = dict(Missao.objects.values_list('codigo', 'pontos'))
        self.assertEqual(
            pontos, {'limpe-bueiro': 50, 'reporte-lixo': 20, 'plante-muda': 80, 'salve-abrigo': 10}
        )

    def test_pontos_da_missao_so_uma_vez(self):
        self.concluir()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.concluir()

    def test_editar_a_missao_nao_muda_os_pontos_ganhos(self):
        concluida = self.concluir()
        Missao.objects.filter(pk=self.missao.pk).update(pontos=999)
        concluida.refresh_from_db()
        self.assertEqual(concluida.pontos, 10)

    def test_missao_ja_concluida_nao_pode_ser_apagada(self):
        self.concluir()
        with self.assertRaises(ProtectedError):
            self.missao.delete()

    def test_excluir_conta_tira_os_pontos_e_mantem_o_relato_anonimo(self):
        self.concluir()
        relato = RelatoLixo.objects.create(morador=self.morador, local='Rua Tal', descricao='Lixo')

        self.morador.delete()

        relato.refresh_from_db()
        self.assertIsNone(relato.morador)
        self.assertFalse(MissaoConcluida.objects.exists())
