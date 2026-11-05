from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import Usuario
from .serializers import TEXTO_CONSENTIMENTO

CADASTRO = '/api/auth/cadastro/'
LOGIN = '/api/auth/login/'
ME = '/api/me/'
DADOS = {
    'email': 'Maria@Exemplo.com',
    'senha': 'chuva-forte-2026',
    'telefone': '(32) 99999-0000',
    'endereco': 'Rua Tal, 10, Centro',
    'consentimento': True,
}


class Base(APITestCase):
    def setUp(self):
        cache.clear()  # zera o limite de tentativas entre os testes


class CadastroTestes(Base):
    def test_cria_morador_com_senha_em_hash_e_consentimento(self):
        resposta = self.client.post(CADASTRO, DADOS, format='json')
        self.assertEqual(resposta.status_code, 201)
        self.assertNotIn('senha', resposta.data)
        usuario = Usuario.objects.get()
        self.assertEqual(usuario.email, 'maria@exemplo.com')
        self.assertEqual(usuario.telefone, '32999990000')
        self.assertNotEqual(usuario.password, DADOS['senha'])
        self.assertTrue(usuario.check_password(DADOS['senha']))
        self.assertIsNotNone(usuario.consentimento_em)
        self.assertEqual(usuario.consentimento_texto, TEXTO_CONSENTIMENTO)

    def test_cadastro_nunca_cria_administrador(self):
        self.client.post(
            CADASTRO, {**DADOS, 'is_staff': True, 'is_superuser': True, 'papel': 'admin'}, format='json'
        )
        usuario = Usuario.objects.get()
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(usuario.papel, 'morador')

    def test_exige_consentimento(self):
        resposta = self.client.post(CADASTRO, {**DADOS, 'consentimento': False}, format='json')
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('consentimento', resposta.data)
        self.assertFalse(Usuario.objects.exists())

    def test_recusa_email_repetido_mesmo_com_outra_caixa(self):
        self.client.post(CADASTRO, DADOS, format='json')
        resposta = self.client.post(CADASTRO, {**DADOS, 'email': 'MARIA@exemplo.com'}, format='json')
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('email', resposta.data)

    def test_recusa_senha_fraca_e_telefone_invalido(self):
        resposta = self.client.post(
            CADASTRO, {**DADOS, 'senha': '12345678', 'telefone': '123'}, format='json'
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('senha', resposta.data)
        self.assertIn('telefone', resposta.data)


class LoginTestes(Base):
    def setUp(self):
        super().setUp()
        Usuario.objects.create_superuser('admin@exemplo.com', 'senha-do-painel-1')
        Usuario.objects.create_user('morador@exemplo.com', 'senha-do-app-1')

    def entrar(self, email, senha):
        return self.client.post(LOGIN, {'email': email, 'password': senha}, format='json')

    def test_cada_conta_recebe_o_seu_papel(self):
        self.assertEqual(self.entrar('admin@exemplo.com', 'senha-do-painel-1').data['papel'], 'admin')
        self.assertEqual(self.entrar('morador@exemplo.com', 'senha-do-app-1').data['papel'], 'morador')

    def test_senha_de_uma_conta_nao_abre_a_outra(self):
        self.assertEqual(self.entrar('admin@exemplo.com', 'senha-do-app-1').status_code, 401)
        self.assertEqual(self.entrar('morador@exemplo.com', 'senha-do-painel-1').status_code, 401)

    def test_mesma_mensagem_para_email_ou_senha_errados(self):
        senha_errada = self.entrar('admin@exemplo.com', 'errada')
        sem_conta = self.entrar('ninguem@exemplo.com', 'errada')
        self.assertEqual(senha_errada.data, sem_conta.data)

    def test_conta_desativada_nao_entra(self):
        Usuario.objects.filter(email='morador@exemplo.com').update(is_active=False)
        self.assertEqual(self.entrar('morador@exemplo.com', 'senha-do-app-1').status_code, 401)

    def test_limita_tentativas_de_senha(self):
        respostas = [self.entrar('admin@exemplo.com', 'errada').status_code for _ in range(11)]
        self.assertEqual(respostas[-1], 429)

    def test_me_exige_token_e_devolve_o_papel_do_banco(self):
        self.assertEqual(self.client.get(ME).status_code, 401)
        token = self.entrar('admin@exemplo.com', 'senha-do-painel-1').data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(self.client.get(ME).data['papel'], 'admin')
        Usuario.objects.filter(email='admin@exemplo.com').update(is_staff=False)
        self.assertEqual(self.client.get(ME).data['papel'], 'morador')

    def test_token_invalido_e_recusado(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer inventado')
        self.assertEqual(self.client.get(ME).status_code, 401)
