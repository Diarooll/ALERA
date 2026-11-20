import json

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings

from ..middleware import ip_do_visitante
from .base import CLOUDFLARE, CLOUDFLARE_2, LOGIN


@override_settings(ALERA_NUM_PROXIES=0, ALERA_ATRAS_DA_CLOUDFLARE=False)
class IpDoVisitanteTests(SimpleTestCase):
    def test_sem_proxy_ignora_cabecalhos_que_o_visitante_escreve(self):
        meta = {
            'REMOTE_ADDR': '203.0.113.5',
            'HTTP_X_FORWARDED_FOR': '1.2.3.4',
            'HTTP_CF_CONNECTING_IP': '5.6.7.8',
        }
        self.assertEqual(ip_do_visitante(meta), '203.0.113.5')

    @override_settings(ALERA_ATRAS_DA_CLOUDFLARE=True)
    def test_cloudflare_entrega_o_ip_do_visitante(self):
        meta = {'REMOTE_ADDR': CLOUDFLARE, 'HTTP_CF_CONNECTING_IP': '198.51.100.7'}
        self.assertEqual(ip_do_visitante(meta), '198.51.100.7')

    @override_settings(ALERA_ATRAS_DA_CLOUDFLARE=True)
    def test_cabecalho_da_cloudflare_vindo_de_fora_dela_nao_vale(self):
        # Alguém que chega direto ao servidor e finge ser a Cloudflare
        meta = {'REMOTE_ADDR': '203.0.113.5', 'HTTP_CF_CONNECTING_IP': '198.51.100.7'}
        self.assertEqual(ip_do_visitante(meta), '203.0.113.5')

    @override_settings(ALERA_ATRAS_DA_CLOUDFLARE=True)
    def test_cabecalho_da_cloudflare_invalido_fica_com_o_ip_da_conexao(self):
        meta = {'REMOTE_ADDR': CLOUDFLARE, 'HTTP_CF_CONNECTING_IP': 'nao-e-ip'}
        self.assertEqual(ip_do_visitante(meta), CLOUDFLARE)

    @override_settings(ALERA_NUM_PROXIES=1)
    def test_proxy_de_confianca_usa_o_ultimo_do_x_forwarded_for(self):
        meta = {'REMOTE_ADDR': '10.0.0.1', 'HTTP_X_FORWARDED_FOR': '1.2.3.4, 198.51.100.7'}
        self.assertEqual(ip_do_visitante(meta), '198.51.100.7')

    @override_settings(ALERA_NUM_PROXIES=1, ALERA_ATRAS_DA_CLOUDFLARE=True)
    def test_cloudflare_e_mais_um_proxy(self):
        # Visitante -> Cloudflare -> proxy da hospedagem -> Django
        meta = {
            'REMOTE_ADDR': '10.0.0.1',
            'HTTP_X_FORWARDED_FOR': f'1.2.3.4, 198.51.100.7, {CLOUDFLARE}',
            'HTTP_CF_CONNECTING_IP': '198.51.100.7',
        }
        self.assertEqual(ip_do_visitante(meta), '198.51.100.7')

    @override_settings(ALERA_NUM_PROXIES=1, ALERA_ATRAS_DA_CLOUDFLARE=True)
    def test_quem_pula_a_cloudflare_e_contado_pelo_proprio_ip(self):
        # Chega direto no proxy da hospedagem, sem passar pela Cloudflare
        meta = {
            'REMOTE_ADDR': '10.0.0.1',
            'HTTP_X_FORWARDED_FOR': '203.0.113.9',
            'HTTP_CF_CONNECTING_IP': '198.51.100.7',
        }
        self.assertEqual(ip_do_visitante(meta), '203.0.113.9')

    def test_ipv6_do_mesmo_bloco_conta_como_um_ip(self):
        um = ip_do_visitante({'REMOTE_ADDR': '2001:db8:1:2::1'})
        outro = ip_do_visitante({'REMOTE_ADDR': '2001:db8:1:2:abcd:ef01:2345:6789'})
        vizinho = ip_do_visitante({'REMOTE_ADDR': '2001:db8:1:3::1'})

        self.assertEqual(um, '2001:db8:1:2::')
        self.assertEqual(um, outro)
        self.assertNotEqual(um, vizinho)

    def test_ipv4_escrito_como_ipv6_e_o_mesmo_ipv4(self):
        self.assertEqual(ip_do_visitante({'REMOTE_ADDR': '::ffff:203.0.113.5'}), '203.0.113.5')


class LimiteDeTentativasPorVisitanteTests(TestCase):
    def setUp(self):
        cache.clear()  # zera o limite de tentativas entre os testes

    def tentar(self, endereco=LOGIN, **meta):
        dados = {'email': 'ninguem@exemplo.com', 'password': 'errada'}
        if endereco == LOGIN:
            return self.client.post(endereco, dados, content_type='application/json', **meta).status_code
        dados = {'username': dados['email'], 'password': dados['password']}
        return self.client.post(endereco, dados, **meta).status_code

    @override_settings(ALERA_ATRAS_DA_CLOUDFLARE=True)
    def test_cloudflare_conta_cada_visitante_a_parte(self):
        # Os pedidos chegam por servidores diferentes da Cloudflare, mas o visitante é o mesmo
        respostas = [
            self.tentar(
                REMOTE_ADDR=CLOUDFLARE if i % 2 else CLOUDFLARE_2,
                HTTP_CF_CONNECTING_IP='198.51.100.7',
            )
            for i in range(11)
        ]
        outro_visitante = self.tentar(REMOTE_ADDR=CLOUDFLARE, HTTP_CF_CONNECTING_IP='198.51.100.8')

        self.assertEqual(respostas[-1], 429)
        self.assertEqual(outro_visitante, 401)

    @override_settings(ALERA_ATRAS_DA_CLOUDFLARE=True)
    def test_falsificar_o_cabecalho_da_cloudflare_nao_escapa_do_limite(self):
        respostas = [
            self.tentar(REMOTE_ADDR='203.0.113.5', HTTP_CF_CONNECTING_IP=f'198.51.100.{i}')
            for i in range(11)
        ]
        self.assertEqual(respostas[-1], 429)

    def test_trocar_de_ipv6_dentro_do_bloco_nao_escapa_do_limite(self):
        respostas = [self.tentar(REMOTE_ADDR=f'2001:db8:1:2::{i + 1:x}') for i in range(11)]
        self.assertEqual(respostas[-1], 429)

    def test_login_do_admin_tambem_conta_pelo_bloco_ipv6(self):
        respostas = [
            self.tentar('/admin/login/', REMOTE_ADDR=f'2001:db8:1:2::{i + 1:x}') for i in range(11)
        ]
        self.assertEqual(respostas[-1], 429)


class LimiteDoCorpoTests(SimpleTestCase):
    def test_json_grande_demais_e_recusado_antes_de_ler(self):
        corpo = json.dumps({'email': 'a' * settings.DATA_UPLOAD_MAX_MEMORY_SIZE, 'password': 'x'})
        resposta = self.client.post(LOGIN, corpo, content_type='application/json')

        self.assertEqual(resposta.status_code, 413)
        self.assertEqual(resposta.json(), {'detail': 'O pedido é grande demais.'})

    def test_arquivo_grande_tambem_e_recusado(self):
        # O limite do Django sozinho não conta arquivo enviado; este conta o pedido inteiro
        arquivo = SimpleUploadedFile('grande.bin', b'0' * (settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 1))
        resposta = self.client.post('/api/auth/cadastro/', {'arquivo': arquivo})

        self.assertEqual(resposta.status_code, 413)
