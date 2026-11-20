from datetime import timedelta

from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from ..models import Usuario


LOGIN = '/api/auth/login/'


RENOVAR = '/api/auth/renovar/'


SAIR = '/api/auth/sair/'


ME = '/api/me/'


EMAIL = 'morador@exemplo.com'


SENHA = 'senha-do-app-1'


class SessaoTestes(APITestCase):
    def setUp(self):
        cache.clear()  # zera os limites de tentativas entre os testes
        self.usuario = Usuario.objects.create_user(EMAIL, SENHA)

    def entrar(self):
        resposta = self.client.post(LOGIN, {'email': EMAIL, 'password': SENHA}, format='json')
        self.assertEqual(resposta.status_code, 200)
        return resposta.data

    def renovar(self, renovacao):
        return self.client.post(RENOVAR, {'renovacao': renovacao}, format='json')

    def ver_perfil(self, token):
        return self.client.get(ME, HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_login_devolve_token_renovacao_e_papel(self):
        dados = self.entrar()
        self.assertEqual(set(dados), {'token', 'renovacao', 'papel'})
        self.assertEqual(dados['papel'], 'morador')
        self.assertEqual(self.ver_perfil(dados['token']).status_code, 200)

    def test_token_de_acesso_vence_rapido_e_a_renovacao_dura_30_dias(self):
        dados = self.entrar()
        acesso = AccessToken(dados['token'])
        renovacao = RefreshToken(dados['renovacao'])
        self.assertEqual(acesso['exp'] - acesso['iat'], int(timedelta(minutes=20).total_seconds()))
        self.assertEqual(renovacao['exp'] - renovacao['iat'], int(timedelta(days=30).total_seconds()))

    def duracao(self, renovacao):
        token = RefreshToken(renovacao)
        return timedelta(seconds=token['exp'] - token['iat'])

    def test_renovar_conta_de_novo_os_30_dias_do_morador(self):
        dados = self.renovar(self.entrar()['renovacao']).data
        self.assertEqual(self.duracao(dados['renovacao']), timedelta(days=30))

    def test_sessao_de_administrador_dura_12_horas_e_renova_com_o_mesmo_prazo(self):
        Usuario.objects.create_user('adm@exemplo.com', 'senha-do-painel-1', is_staff=True)
        dados = self.client.post(
            LOGIN, {'email': 'adm@exemplo.com', 'password': 'senha-do-painel-1'}, format='json'
        ).data
        self.assertEqual(dados['papel'], 'admin')
        self.assertEqual(self.duracao(dados['renovacao']), timedelta(hours=12))
        renovado = self.renovar(dados['renovacao']).data
        self.assertEqual(self.duracao(renovado['renovacao']), timedelta(hours=12))

    def test_login_marca_o_ultimo_acesso(self):
        self.assertIsNone(self.usuario.last_login)
        self.entrar()
        self.usuario.refresh_from_db()
        self.assertIsNotNone(self.usuario.last_login)

    def test_renovar_devolve_um_par_novo_que_funciona(self):
        dados = self.entrar()
        resposta = self.renovar(dados['renovacao'])
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(set(resposta.data), {'token', 'renovacao'})
        self.assertNotEqual(resposta.data['renovacao'], dados['renovacao'])
        self.assertEqual(self.ver_perfil(resposta.data['token']).status_code, 200)

    def test_renovar_nao_pede_o_token_de_acesso(self):
        # O de acesso pode já ter vencido: quem prova a sessão é o de renovação
        dados = self.entrar()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer vencido')
        self.assertEqual(self.renovar(dados['renovacao']).status_code, 200)

    def test_renovacao_ja_usada_nao_vale_de_novo(self):
        dados = self.entrar()
        nova = self.renovar(dados['renovacao']).data['renovacao']
        self.assertEqual(self.renovar(dados['renovacao']).status_code, 401)
        # A nova continua valendo, e gira de novo
        self.assertEqual(self.renovar(nova).status_code, 200)

    def test_depois_de_sair_a_renovacao_nao_vale(self):
        dados = self.entrar()
        self.assertEqual(self.client.post(SAIR, {'renovacao': dados['renovacao']}, format='json').status_code, 204)
        self.assertEqual(self.renovar(dados['renovacao']).status_code, 401)

    def test_sair_de_uma_sessao_nao_derruba_a_outra(self):
        celular = self.entrar()
        computador = self.entrar()
        self.client.post(SAIR, {'renovacao': celular['renovacao']}, format='json')
        self.assertEqual(self.renovar(computador['renovacao']).status_code, 200)

    def test_conta_desativada_nao_renova(self):
        dados = self.entrar()
        Usuario.objects.filter(pk=self.usuario.pk).update(is_active=False)
        self.assertEqual(self.renovar(dados['renovacao']).status_code, 401)

    def test_conta_apagada_nao_renova(self):
        dados = self.entrar()
        self.usuario.delete()
        self.assertEqual(self.renovar(dados['renovacao']).status_code, 401)

    def test_trocar_a_senha_derruba_as_sessoes_abertas(self):
        dados = self.entrar()
        self.usuario.set_password('outra-senha-forte-2026')
        self.usuario.save()
        self.assertEqual(self.renovar(dados['renovacao']).status_code, 401)
        self.assertEqual(self.ver_perfil(dados['token']).status_code, 401)

    def test_token_de_acesso_nao_serve_para_renovar(self):
        dados = self.entrar()
        self.assertEqual(self.renovar(dados['token']).status_code, 401)

    def test_renovacao_falsa_ou_vazia_e_recusada(self):
        self.assertEqual(self.renovar('inventado').status_code, 401)
        self.assertEqual(self.client.post(RENOVAR, {}, format='json').status_code, 400)
        self.assertEqual(self.client.post(SAIR, {'renovacao': 'inventado'}, format='json').status_code, 401)

    def test_limita_renovacoes_seguidas(self):
        respostas = [self.renovar('inventado').status_code for _ in range(31)]
        self.assertEqual(respostas[:30], [401] * 30)
        self.assertEqual(respostas[-1], 429)
