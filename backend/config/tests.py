import importlib.util
import json
import os
import re
from io import StringIO
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.utils import get_random_secret_key
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .middleware import ip_do_visitante

LOGIN = '/api/auth/login/'
CLOUDFLARE = '173.245.48.10'  # um IP de dentro das faixas da Cloudflare
CLOUDFLARE_2 = '162.158.1.2'  # outro, como se fosse outro servidor dela


class SaudeTests(SimpleTestCase):
    def test_responde_sem_login(self):
        resposta = self.client.get('/api/saude/')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {'status': 'ok'})


class UsuarioTests(TestCase):
    def test_projeto_usa_o_usuario_do_alera(self):
        usuario = get_user_model().objects.create_user('teste@exemplo.com', 's3nh4-de-teste')

        self.assertEqual(usuario._meta.label, 'usuarios.Usuario')
        self.assertTrue(usuario.check_password('s3nh4-de-teste'))


def settings_de_producao(**ambiente):
    """Lê o settings.py de novo, à parte, como se estivesse em produção (variáveis falsas).

    O settings de verdade já foi lido com as variáveis desta máquina. Assim dá para conferir
    o modo de produção sem mexer nele nem em nenhum .env.
    """
    variaveis = {
        'DJANGO_DEBUG': 'false',
        'DJANGO_SECRET_KEY': get_random_secret_key(),
        'DATABASE_URL': 'sqlite:///producao-de-teste.sqlite3',
        'DJANGO_ALLOWED_HOSTS': 'alera.exemplo',
        'DJANGO_NUM_PROXIES': '0',
        'DJANGO_ATRAS_DA_CLOUDFLARE': 'false',
        'DJANGO_SECURE_SSL_REDIRECT': 'true',
        **ambiente,
    }
    arquivo = Path(settings.BASE_DIR) / 'config' / 'settings.py'
    spec = importlib.util.spec_from_file_location('settings_de_producao', arquivo)
    modulo = importlib.util.module_from_spec(spec)
    with mock.patch.dict(os.environ, variaveis):
        spec.loader.exec_module(modulo)
    return modulo


# O que muda entre desenvolvimento e produção, para repetir nos testes de resposta
NOMES_DE_PRODUCAO = [
    'SECURE_SSL_REDIRECT',
    'SECURE_REDIRECT_EXEMPT',
    'SECURE_HSTS_SECONDS',
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    'SESSION_COOKIE_SECURE',
    'CSRF_COOKIE_SECURE',
    'SECURE_CSP',
    'SECURE_PROXY_SSL_HEADER',
]


def como_em_producao(**ambiente):
    producao = settings_de_producao(**ambiente)
    return {nome: getattr(producao, nome, None) for nome in NOMES_DE_PRODUCAO}


class ConfiguracaoDeProducaoTests(SimpleTestCase):
    def test_liga_https_hsts_cookies_seguros_e_csp(self):
        producao = settings_de_producao()

        self.assertTrue(producao.SECURE_SSL_REDIRECT)
        self.assertGreaterEqual(producao.SECURE_HSTS_SECONDS, 60 * 60 * 24 * 365)
        self.assertTrue(producao.SECURE_HSTS_INCLUDE_SUBDOMAINS)
        self.assertTrue(producao.SESSION_COOKIE_SECURE)
        self.assertTrue(producao.CSRF_COOKIE_SECURE)
        self.assertEqual(producao.SECURE_CSP, producao.POLITICA_DA_API)

    def test_sem_proxy_nao_acredita_no_x_forwarded_proto(self):
        # Sem proxy, quem escreve esse cabeçalho é o próprio visitante
        self.assertFalse(hasattr(settings_de_producao(), 'SECURE_PROXY_SSL_HEADER'))

    def test_com_proxy_ou_cloudflare_acredita_no_x_forwarded_proto(self):
        esperado = ('HTTP_X_FORWARDED_PROTO', 'https')
        cloudflare = settings_de_producao(DJANGO_ATRAS_DA_CLOUDFLARE='true')
        proxy = settings_de_producao(DJANGO_NUM_PROXIES='1')

        self.assertEqual(cloudflare.SECURE_PROXY_SSL_HEADER, esperado)
        self.assertEqual(proxy.SECURE_PROXY_SSL_HEADER, esperado)

    def test_num_proxies_negativo_e_recusado(self):
        with self.assertRaises(ImproperlyConfigured):
            settings_de_producao(DJANGO_NUM_PROXIES='-1')

    def test_desenvolvimento_continua_em_http(self):
        desenvolvimento = settings_de_producao(DJANGO_DEBUG='true')

        self.assertFalse(getattr(desenvolvimento, 'SECURE_SSL_REDIRECT', False))
        self.assertFalse(getattr(desenvolvimento, 'SESSION_COOKIE_SECURE', False))
        self.assertFalse(hasattr(desenvolvimento, 'SECURE_CSP'))

    def test_check_deploy_nao_tem_avisos(self):
        producao = settings_de_producao()
        with self.settings(
            **como_em_producao(),
            SECRET_KEY=producao.SECRET_KEY,
            ALLOWED_HOSTS=producao.ALLOWED_HOSTS,
        ):
            # Falha (SystemCheckError) se sobrar qualquer aviso
            call_command('check', deploy=True, fail_level='WARNING', stdout=StringIO())


class CabecalhosDeProducaoTests(TestCase):
    def setUp(self):
        cache.clear()  # zera o limite de tentativas do login do /admin/
        valores = self.settings(**como_em_producao())
        valores.enable()
        self.addCleanup(valores.disable)

    def test_api_responde_com_todos_os_cabecalhos(self):
        resposta = self.client.get('/api/saude/', secure=True)

        self.assertEqual(resposta['Strict-Transport-Security'], 'max-age=31536000; includeSubDomains')
        self.assertEqual(
            resposta['Content-Security-Policy'],
            "default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
        )
        self.assertEqual(resposta['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(resposta['X-Frame-Options'], 'DENY')
        self.assertEqual(resposta['Referrer-Policy'], 'same-origin')
        self.assertEqual(resposta['Cross-Origin-Opener-Policy'], 'same-origin')

    def test_http_vira_https(self):
        resposta = self.client.get('/api/me/')

        self.assertEqual(resposta.status_code, 301)
        self.assertEqual(resposta['Location'], 'https://testserver/api/me/')

    def test_teste_de_saude_da_hospedagem_funciona_por_http(self):
        self.assertEqual(self.client.get('/api/saude/').status_code, 200)

    def test_cookies_do_admin_sao_seguros(self):
        get_user_model().objects.create_superuser('adm@exemplo.com', 'senha-do-adm-1')
        self.client.get('/admin/login/', secure=True)
        resposta = self.client.post(
            '/admin/login/',
            {'username': 'adm@exemplo.com', 'password': 'senha-do-adm-1', 'next': '/admin/'},
            secure=True,
        )

        self.assertEqual(resposta.status_code, 302)
        for nome in ('sessionid', 'csrftoken'):
            with self.subTest(cookie=nome):
                cookie = resposta.cookies[nome]
                self.assertTrue(cookie['secure'])
                self.assertTrue(cookie['httponly'])
                self.assertEqual(cookie['samesite'], 'Lax')
        self.assertEqual(resposta.cookies['sessionid']['max-age'], 60 * 60 * 8)


def trechos_que_a_csp_bloquearia(html, nonce):
    """Procura no HTML o que a CSP do /admin/ barraria e quebraria a página."""
    bloqueados = []
    marca = f'nonce="{nonce}"' if nonce else None
    for atributos in re.findall(r'<script\b([^>]*)>', html):
        de_arquivo = re.search(r'\bsrc="/', atributos)
        so_dados = 'type="application/json"' in atributos  # dados, o navegador não executa
        if not (de_arquivo or so_dados or (marca and marca in atributos)):
            bloqueados.append(f'<script{atributos}>')
    for atributos in re.findall(r'<style\b([^>]*)>', html):
        if not (marca and marca in atributos):
            bloqueados.append(f'<style{atributos}>')
    bloqueados += re.findall(r'<[^>]*\sstyle="[^>]*>', html)
    bloqueados += re.findall(r'<[^>]*\son[a-z]+="[^>]*>', html)
    bloqueados += re.findall(r'<link\b[^>]*\bhref="(?!/)[^"]*"[^>]*>', html)
    return bloqueados


class CspDoAdminTests(TestCase):
    def setUp(self):
        self.adm = get_user_model().objects.create_superuser('adm@exemplo.com', 'senha-do-adm-1')

    def conferir(self, endereco):
        resposta = self.client.get(endereco)
        self.assertEqual(resposta.status_code, 200)
        politica = resposta['Content-Security-Policy']
        self.assertIn("default-src 'self'", politica)
        self.assertIn("frame-ancestors 'none'", politica)
        self.assertIn("object-src 'none'", politica)
        nonce = re.search(r"'nonce-([^']+)'", politica)
        nonce = nonce.group(1) if nonce else None
        self.assertEqual(trechos_que_a_csp_bloquearia(resposta.content.decode(), nonce), [])
        return nonce

    def test_login_do_admin_tem_csp_com_nonce(self):
        nonce = self.conferir('/admin/login/')

        self.assertTrue(nonce)

    def test_nonce_muda_a_cada_pagina(self):
        self.assertNotEqual(self.conferir('/admin/login/'), self.conferir('/admin/login/'))

    def test_nenhuma_pagina_do_admin_seria_quebrada_pela_csp(self):
        # Abre a lista, a tela de criar e a de editar de cada modelo do /admin/
        self.client.force_login(self.adm)
        pedido = RequestFactory().get('/admin/')
        pedido.user = self.adm
        enderecos = ['/admin/', '/admin/password_change/']
        for modelo, modelo_admin in admin.site._registry.items():
            rota = f'admin:{modelo._meta.app_label}_{modelo._meta.model_name}'
            enderecos.append(reverse(f'{rota}_changelist'))
            if modelo_admin.has_add_permission(pedido):  # alguns são só para consulta
                enderecos.append(reverse(f'{rota}_add'))
            objeto = modelo_admin.get_queryset(pedido).first()
            if objeto is not None:
                enderecos.append(reverse(f'{rota}_change', args=[objeto.pk]))

        for endereco in enderecos:
            with self.subTest(endereco=endereco):
                self.conferir(endereco)


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
