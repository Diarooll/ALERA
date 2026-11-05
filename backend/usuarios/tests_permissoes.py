from django.test import TestCase
from rest_framework.test import APITestCase

from locais.models import TipoAbrigo

from .models import Usuario

SENHA = 'chuva-forte-2026'
ADMIN = '/admin/'
LOGIN_ADMIN = '/admin/login/'
NOVA_CONTA = '/admin/usuarios/usuario/add/'


def criar_contas():
    principal = Usuario.objects.create_superuser('principal@exemplo.com', SENHA)
    admzinho = Usuario.objects.create_user('admzinho@exemplo.com', SENHA, is_staff=True)
    morador = Usuario.objects.create_user('morador@exemplo.com', SENHA)
    return principal, admzinho, morador


class AdminDoDjangoTestes(TestCase):
    def setUp(self):
        self.principal, self.admzinho, self.morador = criar_contas()

    def test_so_o_adm_principal_abre_o_admin(self):
        esperado = [(self.principal, 200), (self.admzinho, 302), (self.morador, 302)]
        for usuario, status in esperado:
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(ADMIN).status_code, status, usuario.email)

    def test_so_o_adm_principal_passa_pela_tela_de_login(self):
        esperado = [(self.principal, True), (self.admzinho, False), (self.morador, False)]
        for usuario, entrou in esperado:
            self.client.logout()
            self.client.post(LOGIN_ADMIN, {'username': usuario.email, 'password': SENHA})
            self.assertEqual('_auth_user_id' in self.client.session, entrou, usuario.email)

    def test_conta_criada_pelo_adm_principal_nasce_admzinho(self):
        self.client.force_login(self.principal)
        self.client.post(
            NOVA_CONTA,
            {
                'email': 'novo@exemplo.com',
                'usable_password': 'true',
                'password1': SENHA,
                'password2': SENHA,
            },
        )
        novo = Usuario.objects.get(email='novo@exemplo.com')
        self.assertTrue(novo.is_staff)
        self.assertFalse(novo.is_superuser)
        self.assertEqual(novo.papel, 'admin')

    def test_admzinho_nao_cria_conta(self):
        self.client.force_login(self.admzinho)
        self.client.post(
            NOVA_CONTA,
            {
                'email': 'novo@exemplo.com',
                'usable_password': 'true',
                'password1': SENHA,
                'password2': SENHA,
            },
        )
        self.assertFalse(Usuario.objects.filter(email='novo@exemplo.com').exists())


class PainelProprioTestes(APITestCase):
    def setUp(self):
        self.principal, self.admzinho, self.morador = criar_contas()

    def test_admzinho_faz_o_que_o_painel_permite(self):
        self.client.force_authenticate(self.admzinho)
        self.assertEqual(self.client.get('/api/me/').data['papel'], 'admin')
        self.assertEqual(self.client.get('/api/areas/').status_code, 200)

        tipo = self.client.post('/api/tipos-abrigo/', {'nome': 'Praça', 'icone': '🌳'}, format='json')
        self.assertEqual(tipo.status_code, 201)

        abrigo = self.client.post(
            '/api/abrigos/',
            {'nome': 'Escola', 'tipo': tipo.data['id'], 'latitude': '-21.7642', 'longitude': '-43.3503'},
            format='json',
        )
        self.assertEqual(abrigo.status_code, 201)

        rota = f"/api/abrigos/{abrigo.data['id']}/"
        self.assertEqual(self.client.patch(rota, {'nome': 'Escola 2'}, format='json').status_code, 200)
        self.assertEqual(self.client.delete(rota).status_code, 204)

    def test_morador_nao_faz_o_que_e_do_painel(self):
        self.client.force_authenticate(self.morador)
        self.assertEqual(self.client.get('/api/me/').data['papel'], 'morador')
        self.assertEqual(self.client.get('/api/areas/').status_code, 403)

        tipo = TipoAbrigo.objects.first()
        abrigo = self.client.post(
            '/api/abrigos/',
            {'nome': 'Escola', 'tipo': tipo.id, 'latitude': '-21.7642', 'longitude': '-43.3503'},
            format='json',
        )
        self.assertEqual(abrigo.status_code, 403)
        self.assertEqual(
            self.client.post('/api/tipos-abrigo/', {'nome': 'Praça', 'icone': '🌳'}, format='json').status_code,
            403,
        )
