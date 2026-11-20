from decimal import Decimal

from locais.models import Bairro

from ..models import Usuario
from ..serializers import TEXTO_CONSENTIMENTO
from .base import CADASTRO, DADOS, Base


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
