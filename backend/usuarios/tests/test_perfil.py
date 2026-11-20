from decimal import Decimal

from locais.models import Abrigo, AreaRisco, Bairro, CirculoRisco, TipoAbrigo

from ..models import Usuario
from .base import CADASTRO, DADOS, LOGIN, ME, Base


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

    def test_limita_mudancas_seguidas_no_perfil(self):
        # Cada mudança de endereço consulta o serviço de mapas. Sem limite, uma conta podia
        # mandar mudanças sem parar: prende o servidor e faz o serviço bloquear o ALERA inteiro
        respostas = [
            self.client.patch(ME, {'alertas_ativos': True}, format='json').status_code
            for _ in range(31)
        ]
        self.assertEqual(respostas[:30], [200] * 30)
        self.assertEqual(respostas[-1], 429)
        # Ler o perfil continua livre: o app confere o nível a cada minuto
        self.assertEqual(self.client.get(ME).status_code, 200)

    def test_me_mostra_o_endereco_e_a_posicao_do_proprio_morador(self):
        dados = self.client.get(ME).data
        self.assertEqual(dados['bairro'], 'Centro')
        self.assertEqual(dados['cidade'], 'Juiz de Fora')
        self.assertEqual(dados['cep'], '36010000')
        self.assertEqual(float(dados['latitude']), -21.7642)
        self.assertTrue(dados['localizado'])
        self.assertIsNone(dados['area'])

    def bolinha(self, nome, nivel, latitude, longitude, raio_m):
        area = AreaRisco.objects.create(nome=nome, nivel=nivel, orientacao=f'Orientação {nome}')
        CirculoRisco.objects.create(area=area, latitude=latitude, longitude=longitude, raio_m=raio_m)
        return area

    def test_me_mostra_a_area_que_contem_a_casa(self):
        # A casa fica em -21.7642, -43.3503; 0,001 grau de latitude são uns 111 m
        self.bolinha('Encosta Exemplo', 'alerta', '-21.7650', '-43.3503', 200)
        self.bolinha('Longe Exemplo', 'perigo', '-21.8000', '-43.3503', 200)
        self.assertEqual(
            self.client.get(ME).data['area'],
            {'nome': 'Encosta Exemplo', 'nivel': 'alerta', 'orientacao': 'Orientação Encosta Exemplo'},
        )

    def test_casa_em_duas_areas_mostra_a_mais_grave(self):
        self.bolinha('Atenção Exemplo', 'atencao', '-21.7642', '-43.3503', 300)
        self.bolinha('Perigo Exemplo', 'perigo', '-21.7645', '-43.3500', 300)
        self.assertEqual(self.client.get(ME).data['area']['nome'], 'Perigo Exemplo')

    def test_bairro_ligado_a_area_nao_conta_mais(self):
        area = AreaRisco.objects.create(nome='Encosta Exemplo', nivel='perigo')
        Bairro.objects.filter(nome='Centro').update(area=area)
        self.assertIsNone(self.client.get(ME).data['area'])

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

    def test_salvar_o_mesmo_endereco_mantem_o_pin_marcado(self):
        self.client.patch(ME, {'latitude': -21.75, 'longitude': -43.34}, format='json')
        self.localizar.return_value = None

        # O formulário "Meus dados" sempre envia o endereço inteiro, mesmo sem mudança
        resposta = self.client.patch(
            ME,
            {
                'cep': '36010-000',
                'logradouro': 'Rua Tal',
                'numero': '10',
                'bairro': 'Centro',
                'cidade': 'Juiz de Fora',
            },
            format='json',
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Usuario.objects.get().latitude, Decimal('-21.750000'))
        self.assertEqual(self.localizar.call_count, 1)  # só a do cadastro

    def test_mudar_so_a_cidade_localiza_de_novo(self):
        self.localizar.return_value = (Decimal('-22.000000'), Decimal('-44.000000'))

        resposta = self.client.patch(ME, {'cidade': 'Matias Barbosa'}, format='json')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Usuario.objects.get().latitude, Decimal('-22.000000'))

    def test_busca_usa_o_cep(self):
        self.client.patch(ME, {'numero': '182'}, format='json')
        self.assertEqual(self.localizar.call_args.args, ('Rua Tal', '182', 'Centro', 'Juiz de Fora', '36010000'))

    def test_complemento_entra_no_endereco_mas_nao_move_o_pin(self):
        self.client.patch(ME, {'latitude': -21.75, 'longitude': -43.34}, format='json')
        dados = self.client.patch(ME, {'complemento': ' Casa 12 '}, format='json').data

        self.assertEqual(dados['complemento'], 'Casa 12')
        self.assertEqual(dados['endereco'], 'Rua Tal, 10, Casa 12, Centro, Juiz de Fora')
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
