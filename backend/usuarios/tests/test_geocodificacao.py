import io
from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from rest_framework.test import APITestCase

from .. import servicos
from .base import CADASTRO, DADOS


class GeocodificacaoTestes(APITestCase):
    """A ordem da busca, sem consultar o OpenStreetMap de verdade."""

    def setUp(self):
        for alvo, valor in (('usuarios.servicos.PAUSA_S', 0),):
            patcher = patch(alvo, valor)
            patcher.start()
            self.addCleanup(patcher.stop)

    def buscar(self, respostas):
        """Cada consulta devolve a próxima resposta da lista e guarda o que foi pedido."""
        pedidos = []

        def falso(parametros):
            pedidos.append(parametros)
            return respostas.pop(0) if respostas else None

        with patch('usuarios.servicos._buscar', side_effect=falso):
            posicao = servicos.localizar('Av. Exemplo', '182', 'Centro', 'Rio de Janeiro', '22790000')
        return posicao, pedidos

    def test_numero_achado_no_mapa_vale_direto(self):
        exato = {'lat': '-23.0', 'lon': '-43.4', 'address': {'house_number': '182'}}
        posicao, pedidos = self.buscar([exato])
        self.assertEqual(posicao, (Decimal('-23.000000'), Decimal('-43.400000')))
        self.assertEqual(pedidos, [{'street': '182 Av. Exemplo', 'city': 'Rio de Janeiro'}])

    def test_sem_o_numero_no_mapa_o_cep_vale_mais_que_o_meio_da_rua(self):
        meio_da_rua = {'lat': '-23.1', 'lon': '-43.5', 'address': {}}
        pelo_cep = {'lat': '-23.2', 'lon': '-43.6'}
        posicao, pedidos = self.buscar([meio_da_rua, pelo_cep])
        self.assertEqual(posicao, (Decimal('-23.200000'), Decimal('-43.600000')))
        self.assertEqual(pedidos[1], {'postalcode': '22790-000'})

    def test_sem_cep_no_mapa_fica_o_meio_da_rua(self):
        meio_da_rua = {'lat': '-23.1', 'lon': '-43.5', 'address': {}}
        posicao, _ = self.buscar([meio_da_rua, None])
        self.assertEqual(posicao, (Decimal('-23.100000'), Decimal('-43.500000')))

    def test_nada_achado_tenta_o_texto_livre_e_depois_desiste(self):
        posicao, pedidos = self.buscar([None, None, None])
        self.assertIsNone(posicao)
        self.assertEqual(len(pedidos), 3)
        self.assertIn('q', pedidos[2])

    def test_servico_fora_desiste_na_primeira_falha(self):
        # Sem isso o cadastro esperaria o tempo limite três vezes seguidas
        pedidos = []

        def fora(parametros):
            pedidos.append(parametros)
            raise servicos.ServicoFora

        with patch('usuarios.servicos._buscar', side_effect=fora):
            posicao = servicos.localizar('Av. Exemplo', '182', 'Centro', 'Rio de Janeiro', '22790000')
        self.assertIsNone(posicao)
        self.assertEqual(len(pedidos), 1)

    def test_resposta_fora_do_formato_conta_como_nao_achou(self):
        for corpo in (b'{"error": "Unable to geocode"}', b'["texto"]', b'[]'):
            with self.subTest(corpo=corpo), patch(
                'usuarios.servicos.urllib.request.urlopen', return_value=io.BytesIO(corpo)
            ):
                self.assertIsNone(servicos._buscar({'q': 'Rua Tal'}))

    def test_falha_de_rede_vira_servico_fora(self):
        with patch('usuarios.servicos.urllib.request.urlopen', side_effect=OSError('sem internet')):
            with self.assertRaises(servicos.ServicoFora):
                servicos._buscar({'q': 'Rua Tal'})

    def test_cadastro_continua_quando_o_mapa_esta_fora(self):
        cache.clear()
        with patch('usuarios.servicos.urllib.request.urlopen', side_effect=OSError('sem internet')):
            resposta = self.client.post(CADASTRO, DADOS, format='json')
        self.assertEqual(resposta.status_code, 201)
        self.assertFalse(resposta.data['localizado'])
