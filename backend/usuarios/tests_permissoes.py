from django.test import TestCase
from rest_framework.test import APITestCase

from locais.models import AreaRisco, Nivel, TipoAbrigo

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

    def editar(self, usuario, **campos):
        return self.client.post(
            f'/admin/usuarios/usuario/{usuario.pk}/change/',
            {'email': usuario.email, 'is_active': 'on', **campos},
        )

    def test_adm_principal_nao_ve_morador(self):
        self.client.force_login(self.principal)
        lista = self.client.get('/admin/usuarios/usuario/').content.decode()
        self.assertIn(self.admzinho.email, lista)
        self.assertNotIn(self.morador.email, lista)

        rota = f'/admin/usuarios/usuario/{self.morador.pk}/change/'
        self.assertNotEqual(self.client.get(rota).status_code, 200)

    def test_adm_principal_promove_admzinho_a_adm_principal(self):
        self.client.force_login(self.principal)
        self.assertEqual(self.editar(self.admzinho, is_superuser='on').status_code, 302)
        self.admzinho.refresh_from_db()
        self.assertTrue(self.admzinho.is_superuser)
        self.assertTrue(self.admzinho.is_staff)

    def test_adm_nunca_vira_morador_pelo_admin(self):
        self.client.force_login(self.principal)
        self.editar(self.admzinho, is_staff='')
        self.admzinho.refresh_from_db()
        self.assertTrue(self.admzinho.is_staff)

    def test_menu_do_adm_principal(self):
        self.client.force_login(self.principal)
        liberado = ['locais/arearisco', 'locais/tipoabrigo', 'alertas/previsao', 'alertas/historiconivel']
        for modelo in liberado:
            self.assertEqual(self.client.get(f'{ADMIN}{modelo}/').status_code, 200, modelo)

        fora = [
            'auth/group',
            'locais/abrigo',
            'locais/bairro',
            'locais/rua',
            'missoes/missao',
            'missoes/missaoconcluida',
            'missoes/relatolixo',
        ]
        for modelo in fora:
            self.assertEqual(self.client.get(f'{ADMIN}{modelo}/').status_code, 404, modelo)

    def test_adm_principal_cria_area_e_tipo_de_abrigo(self):
        self.client.force_login(self.principal)
        self.client.post(f'{ADMIN}locais/arearisco/add/', {'nome': 'Zona Norte'})
        self.client.post(f'{ADMIN}locais/tipoabrigo/add/', {'nome': 'Ginásio', 'icone': '🏟'})
        self.assertTrue(AreaRisco.objects.filter(nome='Zona Norte', nivel=Nivel.NORMAL).exists())
        self.assertTrue(TipoAbrigo.objects.filter(nome='Ginásio').exists())

    def test_previsoes_e_historico_sao_so_leitura(self):
        self.client.force_login(self.principal)
        for modelo in ['alertas/previsao', 'alertas/historiconivel']:
            self.assertEqual(self.client.get(f'{ADMIN}{modelo}/add/').status_code, 403, modelo)


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
