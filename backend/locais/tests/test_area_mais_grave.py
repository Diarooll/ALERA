from django.test import TestCase

from .. import servicos
from ..models import RAIO_MAXIMO_M, AreaRisco, CirculoRisco, Nivel
from .base import CASA, METROS_POR_GRAU, a_leste, ao_norte


class AreaMaisGraveTestes(TestCase):
    """O nível do morador vem daqui, e o app pergunta a cada minuto."""

    def area(self, nome, nivel, *bolinhas):
        area = AreaRisco.objects.create(nome=nome, nivel=nivel)
        for (lat, lng), raio_m in bolinhas:
            CirculoRisco.objects.create(area=area, latitude=lat, longitude=lng, raio_m=raio_m)
        return area

    def na_casa(self):
        return servicos.area_mais_grave(*CASA)

    def test_gravidade_vai_do_normal_ao_perigo(self):
        # A ordem do Nivel decide quem é "mais grave": mudar a ordem lá muda o alerta do morador
        ordem = sorted(Nivel.values, key=servicos.GRAVIDADE.get)
        self.assertEqual(ordem, ['normal', 'atencao', 'alerta', 'perigo'])

    def test_bolinha_grande_vale_ate_a_borda_em_qualquer_direcao(self):
        # A conta da casa até o centro da bolinha tem que valer também no limite do raio
        for nome, centro in (
            ('Norte', ao_norte(RAIO_MAXIMO_M - 10)),
            ('Sul', ao_norte(-(RAIO_MAXIMO_M - 10))),
            ('Leste', a_leste(RAIO_MAXIMO_M - 10)),
            ('Oeste', a_leste(-(RAIO_MAXIMO_M - 10))),
        ):
            with self.subTest(nome):
                area = self.area(nome, Nivel.ALERTA, (centro, RAIO_MAXIMO_M))
                self.assertEqual(self.na_casa(), area)
                area.delete()

    def test_bolinha_que_nao_alcanca_a_casa_nao_conta(self):
        self.area('Norte', Nivel.PERIGO, (ao_norte(RAIO_MAXIMO_M + 10), RAIO_MAXIMO_M))
        self.area('Leste', Nivel.PERIGO, (a_leste(RAIO_MAXIMO_M + 10), RAIO_MAXIMO_M))
        self.area('Pequena', Nivel.PERIGO, (ao_norte(120), 100))
        self.assertIsNone(self.na_casa())

    def test_casa_em_duas_areas_vale_a_mais_grave(self):
        self.area('Atenção Exemplo', Nivel.ATENCAO, (CASA, 300))
        perigo = self.area('Perigo Exemplo', Nivel.PERIGO, (ao_norte(100), 300))
        self.assertEqual(self.na_casa(), perigo)

    def test_empate_no_nivel_vale_a_ordem_alfabetica(self):
        self.area('Bairro B', Nivel.ALERTA, (CASA, 300))
        primeira = self.area('Bairro A', Nivel.ALERTA, (ao_norte(50), 300))
        self.assertEqual(self.na_casa(), primeira)

    def test_area_com_varias_bolinhas_na_casa_aparece_uma_vez(self):
        area = self.area('Encosta', Nivel.ALERTA, (CASA, 300), (ao_norte(50), 300))
        self.assertEqual(self.na_casa(), area)

    def test_area_sem_bolinhas_nao_conta(self):
        self.area('Sem desenho', Nivel.PERIGO)
        self.assertIsNone(self.na_casa())

    def test_uma_consulta_so_mesmo_com_a_cidade_cheia_de_areas(self):
        # Áreas longe da casa não precisam nem sair do banco
        for i in range(30):
            self.area(f'Longe {i}', Nivel.PERIGO, (ao_norte(10_000 + 1_000 * i), 500))
        perto = self.area('Perto', Nivel.ATENCAO, (CASA, 200))
        with self.assertNumQueries(1):
            self.assertEqual(self.na_casa(), perto)

    def test_sem_a_casa_no_mapa_nem_consulta_o_banco(self):
        self.area('Encosta', Nivel.PERIGO, (CASA, 300))
        with self.assertNumQueries(0):
            self.assertIsNone(servicos.area_mais_grave(None, None))

    def test_funciona_perto_da_linha_de_data_e_do_polo(self):
        # Fora de Juiz de Fora, mas a conta não pode quebrar onde a longitude dá a volta
        lado = self.area('Linha de data', Nivel.ALERTA, (('-16.500000', '-179.999000'), 1000))
        self.assertEqual(servicos.area_mais_grave('-16.500000', '179.999000'), lado)
        polo = self.area('Polo', Nivel.ALERTA, (('-89.999000', '10.000000'), 1000))
        self.assertEqual(servicos.area_mais_grave('-89.999000', '-170.000000'), polo)
