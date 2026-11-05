from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from rest_framework.test import APITestCase

from locais.models import Abrigo, AreaRisco, Bairro, TipoAbrigo

from .models import Usuario
from .serializers import TEXTO_CONSENTIMENTO

CADASTRO = '/api/auth/cadastro/'
LOGIN = '/api/auth/login/'
ME = '/api/me/'
DADOS = {
    'email': 'Maria@Exemplo.com',
    'senha': 'chuva-forte-2026',
    'telefone': '(32) 99999-0000',
    'cep': '36010-000',
    'logradouro': 'Rua Tal',
    'numero': '10',
    'bairro': 'Centro',
    'cidade': 'Juiz de Fora',
    'consentimento': True,
}


class Base(APITestCase):
    def setUp(self):
        cache.clear()  # zera o limite de tentativas entre os testes
        # Nunca consulta o OpenStreetMap de verdade nos testes
        patcher = patch(
            'usuarios.geocodificacao.localizar',
            return_value=(Decimal('-21.764200'), Decimal('-43.350300')),
        )
        self.localizar = patcher.start()
        self.addCleanup(patcher.stop)


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


    def test_cadastro_cria_bairro_sem_area_e_localiza_a_casa(self):
        resposta = self.client.post(CADASTRO, DADOS, format='json')
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data, {'email': 'maria@exemplo.com', 'localizado': True})
        usuario = Usuario.objects.get()
        self.assertEqual(usuario.cep, '36010000')
        self.assertEqual(usuario.endereco, 'Rua Tal, 10, Centro, Juiz de Fora')
        self.assertEqual(usuario.bairro, Bairro.objects.get(nome='Centro', cidade='Juiz de Fora'))
        self.assertIsNone(usuario.bairro.area)
        self.assertEqual(usuario.latitude, Decimal('-21.764200'))

    def test_cadastro_continua_se_nao_acha_o_endereco(self):
        self.localizar.return_value = None
        resposta = self.client.post(CADASTRO, DADOS, format='json')
        self.assertEqual(resposta.status_code, 201)
        self.assertFalse(resposta.data['localizado'])
        self.assertIsNone(Usuario.objects.get().latitude)

    def test_cadastro_reaproveita_o_bairro(self):
        self.client.post(CADASTRO, DADOS, format='json')
        self.client.post(CADASTRO, {**DADOS, 'email': 'outro@exemplo.com'}, format='json')
        self.assertEqual(Bairro.objects.count(), 1)

    def test_cadastro_recusa_cep_invalido(self):
        resposta = self.client.post(CADASTRO, {**DADOS, 'cep': '123'}, format='json')
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('cep', resposta.data)


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


class PerfilTestes(Base):
    def setUp(self):
        super().setUp()
        self.client.post(CADASTRO, DADOS, format='json')
        token = self.client.post(
            LOGIN, {'email': 'maria@exemplo.com', 'password': DADOS['senha']}, format='json'
        ).data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        tipo = TipoAbrigo.objects.get(nome='Escola')
        self.aberto = Abrigo.objects.create(nome='Escola Exemplo', tipo=tipo)
        self.fechado = Abrigo.objects.create(
            nome='Ginásio Exemplo', tipo=tipo, situacao=Abrigo.Situacao.FECHADO
        )

    def test_me_mostra_o_endereco_e_a_posicao_do_proprio_morador(self):
        dados = self.client.get(ME).data
        self.assertEqual(dados['bairro'], 'Centro')
        self.assertEqual(dados['cidade'], 'Juiz de Fora')
        self.assertEqual(dados['cep'], '36010000')
        self.assertEqual(float(dados['latitude']), -21.7642)
        self.assertTrue(dados['localizado'])
        self.assertIsNone(dados['area'])

    def test_me_mostra_a_area_de_risco_do_bairro(self):
        area = AreaRisco.objects.create(nome='Encosta Exemplo')
        Bairro.objects.filter(nome='Centro').update(area=area)
        self.assertEqual(self.client.get(ME).data['area'], {'nome': 'Encosta Exemplo', 'nivel': 'normal'})

    def test_salva_um_abrigo_aberto_e_troca_por_outro(self):
        resposta = self.client.patch(ME, {'abrigo': self.aberto.pk}, format='json')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Usuario.objects.get().abrigo, self.aberto)
        self.assertEqual(self.client.patch(ME, {'abrigo': None}, format='json').status_code, 200)
        self.assertIsNone(Usuario.objects.get().abrigo)

    def test_nao_salva_abrigo_fechado(self):
        resposta = self.client.patch(ME, {'abrigo': self.fechado.pk}, format='json')
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('abrigo', resposta.data)

    def test_mudar_o_endereco_localiza_de_novo(self):
        self.localizar.return_value = (Decimal('-21.770000'), Decimal('-43.360000'))
        resposta = self.client.patch(
            ME, {'cep': '36015-100', 'logradouro': 'Rua Nova', 'numero': 'S/N', 'bairro': 'Benfica'}, format='json'
        )
        self.assertEqual(resposta.status_code, 200)
        usuario = Usuario.objects.get()
        self.assertEqual(usuario.bairro.nome, 'Benfica')
        self.assertEqual(usuario.endereco, 'Rua Nova, S/N, Benfica, Juiz de Fora')
        self.assertEqual(usuario.latitude, Decimal('-21.770000'))

    def test_endereco_nao_encontrado_limpa_a_posicao_e_pede_o_pin(self):
        self.localizar.return_value = None
        dados = self.client.patch(ME, {'numero': '999'}, format='json').data
        self.assertFalse(dados['localizado'])
        self.assertIsNone(dados['latitude'])

    def test_pin_marcado_no_mapa_vale_mais_que_a_busca(self):
        resposta = self.client.patch(
            ME, {'numero': '999', 'latitude': -21.75, 'longitude': -43.34}, format='json'
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Usuario.objects.get().latitude, Decimal('-21.750000'))
        self.assertEqual(self.localizar.call_count, 1)  # só a do cadastro

    def test_latitude_e_longitude_andam_juntas(self):
        resposta = self.client.patch(ME, {'latitude': -21.75}, format='json')
        self.assertEqual(resposta.status_code, 400)

    def test_nao_deixa_trocar_e_mail_nem_telefone_por_aqui(self):
        self.client.patch(ME, {'email': 'outro@exemplo.com', 'telefone': '32911112222'}, format='json')
        usuario = Usuario.objects.get()
        self.assertEqual(usuario.email, 'maria@exemplo.com')
        self.assertEqual(usuario.telefone, '32999990000')

    def test_nao_deixa_virar_administrador(self):
        self.client.patch(ME, {'is_staff': True, 'papel': 'admin'}, format='json')
        self.assertFalse(Usuario.objects.get().is_staff)
