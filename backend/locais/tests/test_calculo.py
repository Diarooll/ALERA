from django.test import TestCase

from .. import servicos


class CalculoTestes(TestCase):
    def test_distancia_em_linha_reta(self):
        # Um grau de latitude tem uns 111 km
        self.assertAlmostEqual(servicos.distancia_em_metros(-21, -43, -22, -43), 111_195, delta=50)
        self.assertEqual(servicos.distancia_em_metros(-21.76, -43.35, -21.76, -43.35), 0)

    def test_tempo_a_pe_arredonda_para_cima_e_nunca_zera(self):
        self.assertEqual(servicos.tempo_a_pe_min(800), 10)
        self.assertEqual(servicos.tempo_a_pe_min(801), 11)
        self.assertEqual(servicos.tempo_a_pe_min(0), 1)
