from rest_framework.test import APITestCase

from alertas.models import HistoricoNivel
from alertas.servicos import mudar_nivel
from usuarios.models import Usuario

from ..models import Abrigo, AreaRisco, Nivel, Rua


class ApagarAreaTestes(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser('admin@exemplo.com', 'senha-do-painel-1')
        self.client.force_authenticate(self.admin)
        self.area = AreaRisco.objects.create(nome='Encosta Exemplo')

    def apagar(self):
        return self.client.delete(f'/api/areas/{self.area.pk}/')

    def test_abrigo_ligado_pelo_cadastro_antigo_nao_prende_a_area(self):
        # Antes o abrigo pertencia a uma área. O painel nem mostra mais esse vínculo,
        # então ele não pode impedir o admin de apagar a área
        abrigo = Abrigo.objects.create(
            nome='Escola Antiga', area=self.area, latitude='-21.76', longitude='-43.35'
        )
        self.assertEqual(self.apagar().status_code, 204)
        self.assertFalse(AreaRisco.objects.exists())
        abrigo.refresh_from_db()
        self.assertIsNone(abrigo.area)

    def test_area_com_alerta_explica_o_motivo(self):
        mudar_nivel(self.area, Nivel.ALERTA, HistoricoNivel.Origem.DEFESA_CIVIL, self.admin)
        abrigo = Abrigo.objects.create(
            nome='Escola Antiga', area=self.area, latitude='-21.76', longitude='-43.35'
        )
        resposta = self.apagar()
        self.assertEqual(resposta.status_code, 409)
        self.assertIn('alertas', resposta.data['detail'])
        # Nada muda quando a área não pode sair
        abrigo.refresh_from_db()
        self.assertEqual(abrigo.area, self.area)

    def test_morador_nao_cria_muda_nem_apaga_area(self):
        self.client.force_authenticate(Usuario.objects.create_user('m@exemplo.com', 'senha-do-app-1'))
        rota = f'/api/areas/{self.area.pk}/'
        bolinha = {'latitude': '-21.76', 'longitude': '-43.35', 'raio_m': 200}
        self.assertEqual(
            self.client.post('/api/areas/', {'nome': 'Nova', 'circulos': [bolinha]}, format='json').status_code,
            403,
        )
        self.assertEqual(self.client.patch(rota, {'circulos': [bolinha]}, format='json').status_code, 403)
        self.assertEqual(self.client.delete(rota).status_code, 403)
        self.assertFalse(self.area.circulos.exists())
        self.assertTrue(AreaRisco.objects.filter(pk=self.area.pk).exists())

    def test_area_com_rua_antiga_nao_culpa_os_alertas(self):
        Rua.objects.create(nome='Rua Exemplo', bairro='Centro', area=self.area)
        resposta = self.apagar()
        self.assertEqual(resposta.status_code, 409)
        self.assertNotIn('alertas', resposta.data['detail'])
        self.assertIn('ruas', resposta.data['detail'])
        self.assertTrue(AreaRisco.objects.filter(pk=self.area.pk).exists())
