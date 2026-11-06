from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APITestCase

from locais.models import AreaRisco, Nivel, TipoAbrigo

from .models import Usuario

SENHA = 'chuva-forte-2026'
ADMIN = '/admin/'
LOGIN_ADMIN = '/admin/login/'
NOVA_CONTA = '/admin/usuarios/staff/add/'


def criar_contas():
    principal = Usuario.objects.create_superuser('principal@exemplo.com', SENHA)
    admzinho = Usuario.objects.create_user('admzinho@exemplo.com', SENHA, is_staff=True)
    morador = Usuario.objects.create_user('morador@exemplo.com', SENHA)
    return principal, admzinho, morador


class AdminDoDjangoTestes(TestCase):
    def setUp(self):
        cache.clear()  # zera o limite de tentativas da tela de login entre os testes
        self.principal, self.admzinho, self.morador = criar_contas()

    def test_tela_de_login_do_admin_limita_tentativas(self):
        # Sem limite, a senha do ADM principal podia ser chutada sem parar pelo /admin/
        errada = {'username': self.principal.email, 'password': 'chute-errado'}
        respostas = [self.client.post(LOGIN_ADMIN, errada).status_code for _ in range(11)]
        self.assertEqual(respostas[:10], [200] * 10)
        self.assertEqual(respostas[-1], 429)

        # Nem a senha certa entra enquanto o limite vale
        self.client.post(LOGIN_ADMIN, {'username': self.principal.email, 'password': SENHA})
        self.assertNotIn('_auth_user_id', self.client.session)

        # Abrir a tela (sem tentar entrar) não conta como tentativa
        self.assertEqual(self.client.get(LOGIN_ADMIN).status_code, 200)

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
            f'/admin/usuarios/staff/{usuario.pk}/change/',
            {'email': usuario.email, 'is_active': 'on', **campos},
        )

    def test_adm_principal_nao_ve_morador(self):
        self.client.force_login(self.principal)
        lista = self.client.get('/admin/usuarios/staff/').content.decode()
        self.assertIn(self.admzinho.email, lista)
        self.assertNotIn(self.morador.email, lista)

        rota = f'/admin/usuarios/staff/{self.morador.pk}/change/'
        self.assertNotEqual(self.client.get(rota).status_code, 200)

    def test_moradores_aparecem_so_com_telefone(self):
        self.morador.telefone = '32999990000'
        self.morador.endereco = 'Rua Secreta, 10'
        self.morador.save()
        self.client.force_login(self.principal)

        paginas = [
            '/admin/usuarios/morador/',
            f'/admin/usuarios/morador/{self.morador.pk}/change/',
            '/admin/usuarios/morador/?q=(32)%2099999-0000',
        ]
        for pagina in paginas:
            resposta = self.client.get(pagina)
            self.assertEqual(resposta.status_code, 200, pagina)
            html = resposta.content.decode()
            self.assertIn('(32) 99999-0000', html, pagina)
            self.assertIn(f'Morador nº {self.morador.pk}', html, pagina)
            self.assertNotIn(self.morador.email, html, pagina)
            self.assertNotIn('Rua Secreta', html, pagina)
            self.assertNotIn(self.morador.password, html, pagina)

        # Conta de ADM não entra na lista de moradores
        self.assertNotIn(self.admzinho.email, self.client.get('/admin/usuarios/morador/').content.decode())

    def test_morador_no_admin_e_so_leitura(self):
        self.client.force_login(self.principal)
        rota = f'/admin/usuarios/morador/{self.morador.pk}/'
        self.assertEqual(self.client.get('/admin/usuarios/morador/add/').status_code, 403)
        self.assertEqual(self.client.post(f'{rota}delete/').status_code, 403)

        self.client.post(f'{rota}change/', {'telefone': '11999990000'})
        self.morador.refresh_from_db()
        self.assertEqual(self.morador.telefone, '')

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
        liberado = [
            'usuarios/staff',
            'usuarios/morador',
            'locais/tipoabrigo',
            'alertas/previsao',
            'alertas/historiconivel',
        ]
        for modelo in liberado:
            self.assertEqual(self.client.get(f'{ADMIN}{modelo}/').status_code, 200, modelo)

        inicio = self.client.get(ADMIN).content.decode()
        self.assertIn('Staffs', inicio)
        self.assertIn('Usuários', inicio)

        fora = [
            'usuarios/usuario',
            'auth/group',
            'locais/arearisco',
            'locais/circulorisco',
            'locais/abrigo',
            'locais/bairro',
            'locais/rua',
            'missoes/missao',
            'missoes/missaoconcluida',
            'missoes/relatolixo',
        ]
        for modelo in fora:
            self.assertEqual(self.client.get(f'{ADMIN}{modelo}/').status_code, 404, modelo)

    def test_adm_principal_cria_tipo_de_abrigo(self):
        self.client.force_login(self.principal)
        self.client.post(f'{ADMIN}locais/tipoabrigo/add/', {'nome': 'Ginásio', 'icone': '🏟'})
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

    def test_painel_cria_e_desenha_area_de_risco(self):
        self.client.force_authenticate(self.admzinho)
        bolinhas = [
            {'latitude': '-21.7642', 'longitude': '-43.3503', 'raio_m': 200},
            {'latitude': '-21.7660', 'longitude': '-43.3520', 'raio_m': 350},
        ]
        criada = self.client.post('/api/areas/', {'nome': 'Morro Exemplo', 'circulos': bolinhas}, format='json')
        self.assertEqual(criada.status_code, 201)
        self.assertEqual(len(criada.data['circulos']), 2)
        self.assertEqual(criada.data['nivel'], Nivel.NORMAL)

        rota = f"/api/areas/{criada.data['id']}/"
        # Salvar manda as bolinhas todas juntas e troca as antigas; o nível não muda por aqui
        editada = self.client.patch(rota, {'circulos': bolinhas[:1], 'nivel': 'perigo'}, format='json')
        self.assertEqual(len(editada.data['circulos']), 1)
        self.assertEqual(editada.data['nivel'], Nivel.NORMAL)

        self.assertEqual(self.client.delete(rota).status_code, 204)
        self.assertFalse(AreaRisco.objects.exists())

    def test_bolinha_com_tamanho_fora_do_limite_e_recusada(self):
        self.client.force_authenticate(self.admzinho)
        bolinha = {'latitude': '-21.7642', 'longitude': '-43.3503', 'raio_m': 10}
        resposta = self.client.post('/api/areas/', {'nome': 'Teste', 'circulos': [bolinha]}, format='json')
        self.assertEqual(resposta.status_code, 400)

    def test_area_com_alerta_nao_pode_ser_apagada(self):
        self.client.force_authenticate(self.admzinho)
        area = AreaRisco.objects.create(nome='Morro Exemplo')
        self.client.post('/api/alertas/', {'areas': [area.pk], 'nivel': 'alerta', 'mensagem': 'x'}, format='json')
        self.assertEqual(self.client.delete(f'/api/areas/{area.pk}/').status_code, 409)
        self.assertTrue(AreaRisco.objects.filter(pk=area.pk).exists())

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
