import importlib
from decimal import Decimal
from unittest.mock import patch

from django.apps import apps
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase

from locais.models import Bairro

from .. import servicos
from ..models import Usuario


CADASTRO = '/api/auth/cadastro/'


LOGIN = '/api/auth/login/'


ME = '/api/me/'


SENHA = 'chuva-forte-2026'


DADOS = {
    'email': 'maria@exemplo.com',
    'senha': SENHA,
    'telefone': '(32) 99999-0000',
    'cep': '36010-000',
    'logradouro': 'Rua Tal',
    'numero': '10',
    'bairro': 'Centro',
    'cidade': 'Juiz de Fora',
    'consentimento': True,
}


POSICAO = (Decimal('-21.764200'), Decimal('-43.350300'))


class ComMapaFalso(APITestCase):
    def setUp(self):
        cache.clear()  # zera o limite de tentativas entre os testes
        patcher = patch('usuarios.servicos.localizar', return_value=POSICAO)
        self.localizar = patcher.start()
        self.addCleanup(patcher.stop)

    def cadastrar(self, **campos):
        return self.client.post(CADASTRO, {**DADOS, **campos}, format='json')


class EmailSemCaixaTestes(TestCase):
    """O e-mail vale inteiro em minúsculas em qualquer caminho, não só no cadastro do app."""

    def setUp(self):
        cache.clear()
        self.principal = Usuario.objects.create_superuser('principal@exemplo.com', SENHA)

    def criar_pelo_admin(self, email):
        self.client.force_login(self.principal)
        return self.client.post(
            '/admin/usuarios/staff/add/',
            {'email': email, 'usable_password': 'true', 'password1': SENHA, 'password2': SENHA},
        )

    def test_conta_criada_no_admin_com_maiuscula_entra_no_app(self):
        # O /admin/ só passava o domínio para minúsculas: "Ana@exemplo.com" ficava gravado
        # assim, o login do app procurava "ana@exemplo.com" e o ADMzinho nunca entrava
        self.criar_pelo_admin('Ana@Exemplo.COM')
        self.assertTrue(Usuario.objects.filter(email='ana@exemplo.com').exists())

        resposta = self.client.post(
            LOGIN, {'email': 'ana@exemplo.com', 'password': SENHA}, content_type='application/json'
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()['papel'], 'admin')

    def test_admin_nao_cria_conta_repetida_com_outra_caixa(self):
        Usuario.objects.create_user('maria@exemplo.com', SENHA)
        resposta = self.criar_pelo_admin('MARIA@exemplo.com')
        self.assertEqual(resposta.status_code, 200)  # volta o formulário com o erro
        self.assertEqual(Usuario.objects.filter(email__iexact='maria@exemplo.com').count(), 1)

    def test_login_do_admin_aceita_o_email_com_maiuscula(self):
        self.client.post('/admin/login/', {'username': 'Principal@Exemplo.com', 'password': SENHA})
        self.assertIn('_auth_user_id', self.client.session)

    def test_salvar_por_qualquer_caminho_guarda_em_minusculas(self):
        conta = Usuario(email='  Joao@Exemplo.com ')
        conta.save()
        conta.refresh_from_db()
        self.assertEqual(conta.email, 'joao@exemplo.com')

    def test_banco_recusa_o_mesmo_email_com_outra_caixa(self):
        # bulk_create não passa pelo save(): quem garante é a regra do próprio banco
        Usuario.objects.create_user('maria@exemplo.com', SENHA)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.bulk_create([Usuario(email='Maria@exemplo.com')])

    def test_migracao_passa_as_contas_antigas_para_minusculas(self):
        conta = Usuario.objects.create_user('antiga@exemplo.com', SENHA)
        Usuario.objects.filter(pk=conta.pk).update(email='Antiga@Exemplo.com')

        migracao = importlib.import_module('usuarios.migrations.0007_email_em_minusculas')
        migracao.passar_emails_para_minusculas(apps, None)

        conta.refresh_from_db()
        self.assertEqual(conta.email, 'antiga@exemplo.com')


class CadastroTestes(ComMapaFalso):
    def test_cadastro_com_maiuscula_entra_depois(self):
        self.assertEqual(self.cadastrar(email='  Maria@Gmail.com ').status_code, 201)
        resposta = self.client.post(
            LOGIN, {'email': 'maria@gmail.com', 'password': SENHA}, format='json'
        )
        self.assertEqual(resposta.status_code, 200)

    def test_dois_cadastros_ao_mesmo_tempo_nao_quebram_o_servidor(self):
        # Entre conferir o e-mail e gravar a conta, o cadastro espera o mapa (segundos).
        # Se outro cadastro com o mesmo e-mail termina nesse meio tempo, era erro 500
        def outro_cadastro_termina_antes(*args):
            Usuario.objects.create_user('maria@exemplo.com', SENHA)
            return POSICAO

        self.localizar.side_effect = outro_cadastro_termina_antes
        resposta = self.cadastrar()
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.data, {'email': ['Este e-mail já tem uma conta.']})
        self.assertEqual(Usuario.objects.count(), 1)

    def test_email_maior_que_o_banco_aceita_e_recusado_no_campo(self):
        resposta = self.cadastrar(email=f"{'a' * 250}@exemplo.com")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('email', resposta.data)

    def test_telefone_com_mais_55_vale_como_no_front(self):
        # A máscara do login.js tira o "+55"; quem chama a API direto também pode mandar
        resposta = self.cadastrar(telefone='+55 (32) 99999-0000')
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(Usuario.objects.get().telefone, '32999990000')

    def test_telefone_fixo_vale_e_ddd_com_zero_nao(self):
        self.assertEqual(self.cadastrar(telefone='(32) 3215-0000').status_code, 201)
        self.assertEqual(Usuario.objects.get().telefone, '3232150000')

        resposta = self.cadastrar(email='outra@exemplo.com', telefone='(02) 99999-0000')
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.data['telefone'], ['Telefone inválido. Exemplo: (32) 99999-0000'])

    def test_bairro_com_outra_caixa_e_o_mesmo_bairro(self):
        self.cadastrar()
        self.cadastrar(email='outra@exemplo.com', bairro='CENTRO', cidade='juiz de fora')
        self.assertEqual(Bairro.objects.count(), 1)


class PerfilTestes(ComMapaFalso):
    def setUp(self):
        super().setUp()
        self.cadastrar()
        self.client.force_authenticate(Usuario.objects.get())

    def test_bairro_so_com_outra_caixa_nao_consulta_o_mapa_nem_perde_o_pin(self):
        self.client.patch(ME, {'latitude': -21.75, 'longitude': -43.34}, format='json')
        self.localizar.return_value = None

        resposta = self.client.patch(
            ME,
            {'cep': '36010000', 'logradouro': 'Rua Tal', 'numero': '10', 'bairro': 'centro', 'cidade': 'Juiz de Fora'},
            format='json',
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Bairro.objects.count(), 1)
        self.assertEqual(Usuario.objects.get().latitude, Decimal('-21.750000'))
        self.assertEqual(self.localizar.call_count, 1)  # só a do cadastro

    def test_rua_e_numero_nao_ficam_em_branco(self):
        # O cadastro exige rua e número; o perfil aceitava apagar os dois
        resposta = self.client.patch(ME, {'logradouro': '', 'numero': '  '}, format='json')
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('logradouro', resposta.data)
        self.assertIn('numero', resposta.data)
        self.assertEqual(Usuario.objects.get().logradouro, 'Rua Tal')

    def test_latitude_sem_longitude_avisa_no_campo(self):
        resposta = self.client.patch(ME, {'latitude': -21.75}, format='json')
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.data, {'latitude': ['Envie latitude e longitude juntas.']})


class MapaForaDoArTestes(APITestCase):
    """Sem o serviço de mapas (ou com resposta estranha), cadastro e perfil continuam."""

    def setUp(self):
        cache.clear()
        patcher = patch('usuarios.servicos.PAUSA_S', 0)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_perfil_salva_o_endereco_com_o_mapa_fora(self):
        conta = Usuario.objects.create_user('maria@exemplo.com', SENHA)
        self.client.force_authenticate(conta)
        with patch('usuarios.servicos.urllib.request.urlopen', side_effect=TimeoutError):
            resposta = self.client.patch(
                ME, {'cep': '36010-000', 'logradouro': 'Rua Tal', 'numero': '10', 'bairro': 'Centro', 'cidade': 'Juiz de Fora'}, format='json'
            )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.data['localizado'])
        self.assertEqual(Usuario.objects.get().logradouro, 'Rua Tal')

    def localizar(self, achados):
        with patch('usuarios.servicos._buscar', side_effect=achados):
            return servicos.localizar('Rua Tal', '10', 'Centro', 'Juiz de Fora', '36010000')

    def test_endereco_fora_do_formato_nao_quebra_o_cadastro(self):
        # "address" vindo como null ou texto dava AttributeError, e o cadastro caía com erro 500
        for endereco in (None, 'texto', ['lista']):
            with self.subTest(endereco=endereco):
                meio_da_rua = {'lat': '-21.7', 'lon': '-43.3', 'address': endereco}
                self.assertEqual(
                    self.localizar([meio_da_rua, None]), (Decimal('-21.700000'), Decimal('-43.300000'))
                )

    def test_coordenada_impossivel_conta_como_nao_achou(self):
        # Latitude 999 ou NaN não cabe no banco: no PostgreSQL o cadastro caía com erro 500
        for lat, lon in (('999', '-43.3'), ('-21.7', '-500'), ('NaN', '-43.3')):
            with self.subTest(lat=lat, lon=lon):
                ruim = {'lat': lat, 'lon': lon, 'address': {'house_number': '10'}}
                self.assertIsNone(self.localizar([ruim, None, None]))
