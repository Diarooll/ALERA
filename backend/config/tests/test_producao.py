import re
from io import StringIO

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from .base import NOMES_DE_PRODUCAO, como_em_producao, settings_de_producao, trechos_que_a_csp_bloquearia


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
