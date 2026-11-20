from ..models import Usuario
from .base import LOGIN, ME, Base


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

    def test_limite_nao_cai_trocando_o_cabecalho_de_ip(self):
        # Qualquer um escreve o X-Forwarded-For. Se o limite confiar nele, cada tentativa
        # com um valor diferente conta como outra pessoa e a senha pode ser chutada sem fim
        respostas = [
            self.client.post(
                LOGIN,
                {'email': 'admin@exemplo.com', 'password': 'errada'},
                format='json',
                HTTP_X_FORWARDED_FOR=f'10.0.0.{i}',
            ).status_code
            for i in range(11)
        ]
        self.assertEqual(respostas[-1], 429)

    def test_token_assinado_com_a_chave_antiga_do_repositorio_nao_vale(self):
        # A chave de desenvolvimento ficava escrita no código: quem lesse o repositório
        # conseguia fabricar o token de qualquer conta, inclusive a do ADM principal
        import jwt
        from django.utils import timezone

        admin = Usuario.objects.get(email='admin@exemplo.com')
        falso = jwt.encode(
            {
                'token_type': 'access',
                'user_id': str(admin.pk),
                'jti': 'feito-por-fora',
                'exp': int((timezone.now() + timezone.timedelta(hours=1)).timestamp()),
            },
            'somente-para-desenvolvimento-local',
            algorithm='HS256',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {falso}')
        self.assertEqual(self.client.get(ME).status_code, 401)

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
