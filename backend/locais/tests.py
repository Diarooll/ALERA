from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from rest_framework.test import APITestCase

from usuarios.models import Usuario

from . import servicos

from .models import Abrigo, AreaRisco, Bairro, Rua, TipoAbrigo


class LocaisTestes(TestCase):
    def setUp(self):
        self.area = AreaRisco.objects.create(nome='Área Exemplo')
        self.rua = Rua.objects.create(nome='Rua Exemplo', bairro='Centro', area=self.area)
        self.abrigo = Abrigo.objects.create(
            nome='Escola Exemplo', area=self.area, distancia_m=600, tempo_a_pe_min=8
        )

    def test_area_comeca_em_normal(self):
        self.assertEqual(self.area.nivel, 'normal')

    def test_nivel_invalido_e_recusado_pelo_banco(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AreaRisco.objects.filter(pk=self.area.pk).update(nivel='inventado')

    def test_nao_repete_rua_no_mesmo_bairro(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rua.objects.create(nome='Rua Exemplo', bairro='Centro', area=self.area)
        Rua.objects.create(nome='Rua Exemplo', bairro='São Mateus', area=self.area)

    def test_area_com_rua_nao_pode_ser_apagada(self):
        with self.assertRaises(ProtectedError):
            self.area.delete()

    def test_rua_com_morador_nao_pode_ser_apagada(self):
        Usuario.objects.create_user('morador@exemplo.com', 'senha-do-app-1', rua=self.rua)
        with self.assertRaises(ProtectedError):
            self.rua.delete()

    def test_apagar_abrigo_so_limpa_o_abrigo_salvo(self):
        morador = Usuario.objects.create_user(
            'morador@exemplo.com', 'senha-do-app-1', abrigo=self.abrigo
        )
        self.abrigo.delete()
        morador.refresh_from_db()
        self.assertIsNone(morador.abrigo)


class CalculoTestes(TestCase):
    def test_distancia_em_linha_reta(self):
        # Um grau de latitude tem uns 111 km
        self.assertAlmostEqual(servicos.distancia_em_metros(-21, -43, -22, -43), 111_195, delta=50)
        self.assertEqual(servicos.distancia_em_metros(-21.76, -43.35, -21.76, -43.35), 0)

    def test_tempo_a_pe_arredonda_para_cima_e_nunca_zera(self):
        self.assertEqual(servicos.tempo_a_pe_min(800), 10)
        self.assertEqual(servicos.tempo_a_pe_min(801), 11)
        self.assertEqual(servicos.tempo_a_pe_min(0), 1)


class AbrigoTestes(APITestCase):
    def setUp(self):
        self.tipo = TipoAbrigo.objects.get(nome='Escola')
        self.admin = Usuario.objects.create_superuser('admin@exemplo.com', 'senha-do-painel-1')
        self.maria = Usuario.objects.create_user(
            'maria@exemplo.com', 'senha-do-app-1', latitude='-21.764200', longitude='-43.350300'
        )
        self.joao = Usuario.objects.create_user(
            'joao@exemplo.com', 'senha-do-app-1', latitude='-21.800000', longitude='-43.300000'
        )
        self.sem_casa = Usuario.objects.create_user('sem@exemplo.com', 'senha-do-app-1')
        self.perto = Abrigo.objects.create(
            nome='Escola Perto', tipo=self.tipo, latitude='-21.765000', longitude='-43.350000'
        )
        self.longe = Abrigo.objects.create(
            nome='Igreja Longe', tipo=self.tipo, latitude='-21.790000', longitude='-43.320000'
        )
        self.fechado = Abrigo.objects.create(
            nome='Ginásio Fechado',
            tipo=self.tipo,
            latitude='-21.764500',
            longitude='-43.350100',
            situacao=Abrigo.Situacao.FECHADO,
        )

    def entrar_como(self, usuario):
        self.client.force_authenticate(usuario)

    NOVO = {
        'nome': 'Centro Novo',
        'referencia': 'Rua Exemplo',
        'situacao': 'aberto',
        'latitude': -21.77,
        'longitude': -43.34,
        'capacidade': 120,
    }

    def test_anonimo_nao_ve_nada(self):
        for rota in ('/api/abrigos/', '/api/tipos-abrigo/', '/api/areas/'):
            self.assertEqual(self.client.get(rota).status_code, 401, rota)
        self.assertEqual(self.client.post('/api/abrigos/', self.NOVO, format='json').status_code, 401)

    def test_morador_le_mas_nao_escreve(self):
        self.entrar_como(self.maria)
        self.assertEqual(self.client.get('/api/abrigos/').status_code, 200)
        self.assertEqual(self.client.get('/api/tipos-abrigo/').status_code, 200)
        novo = {**self.NOVO, 'tipo': self.tipo.pk}
        self.assertEqual(self.client.post('/api/abrigos/', novo, format='json').status_code, 403)
        self.assertEqual(
            self.client.patch(f'/api/abrigos/{self.perto.pk}/', {'nome': 'X'}, format='json').status_code, 403
        )
        self.assertEqual(self.client.delete(f'/api/abrigos/{self.perto.pk}/').status_code, 403)
        self.assertEqual(self.client.post('/api/tipos-abrigo/', {'nome': 'Praça'}, format='json').status_code, 403)
        self.assertEqual(self.client.get('/api/areas/').status_code, 403)

    def test_admin_cria_edita_e_apaga_abrigo(self):
        self.entrar_como(self.admin)
        resposta = self.client.post('/api/abrigos/', {**self.NOVO, 'tipo': self.tipo.pk}, format='json')
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data['tipo']['nome'], 'Escola')
        pk = resposta.data['id']
        mover = self.client.patch(f'/api/abrigos/{pk}/', {'latitude': -21.7, 'longitude': -43.3}, format='json')
        self.assertEqual(mover.status_code, 200)
        self.assertEqual(float(Abrigo.objects.get(pk=pk).latitude), -21.7)
        self.assertEqual(self.client.delete(f'/api/abrigos/{pk}/').status_code, 204)

    def test_abrigo_exige_posicao_dentro_do_mapa(self):
        self.entrar_como(self.admin)
        sem = {k: v for k, v in self.NOVO.items() if k != 'longitude'}
        self.assertEqual(
            self.client.post('/api/abrigos/', {**sem, 'tipo': self.tipo.pk}, format='json').status_code, 400
        )
        fora = {**self.NOVO, 'latitude': 123, 'tipo': self.tipo.pk}
        self.assertEqual(self.client.post('/api/abrigos/', fora, format='json').status_code, 400)

    def test_lista_do_mais_perto_ao_mais_longe_e_inclui_fechados(self):
        self.entrar_como(self.maria)
        nomes = [a['nome'] for a in self.client.get('/api/abrigos/').data]
        self.assertEqual(nomes, ['Ginásio Fechado', 'Escola Perto', 'Igreja Longe'])
        primeiro = self.client.get('/api/abrigos/').data[0]
        self.assertEqual(primeiro['situacao'], 'fechado')
        self.assertGreater(primeiro['distancia_m'], 0)
        self.assertGreaterEqual(primeiro['tempo_a_pe_min'], 1)

    def test_cada_morador_recebe_a_distancia_da_propria_casa(self):
        self.entrar_como(self.maria)
        da_maria = {a['nome']: a['distancia_m'] for a in self.client.get('/api/abrigos/').data}
        self.entrar_como(self.joao)
        do_joao = {a['nome']: a['distancia_m'] for a in self.client.get('/api/abrigos/').data}
        self.assertNotEqual(da_maria['Escola Perto'], do_joao['Escola Perto'])

    def test_resposta_nunca_traz_a_posicao_de_moradores(self):
        self.entrar_como(self.maria)
        texto = self.client.get('/api/abrigos/').content.decode()
        for usuario in (self.maria, self.joao):
            self.assertNotIn(str(usuario.latitude), texto)
            self.assertNotIn(usuario.email, texto)

    def test_sem_a_casa_localizada_nao_ha_distancia_e_ordena_por_nome(self):
        self.entrar_como(self.sem_casa)
        dados = self.client.get('/api/abrigos/').data
        self.assertEqual([a['nome'] for a in dados], ['Escola Perto', 'Ginásio Fechado', 'Igreja Longe'])
        self.assertTrue(all(a['distancia_m'] is None for a in dados))

    def test_admin_cria_tipo_novo_e_nao_repete_nome(self):
        self.entrar_como(self.admin)
        self.assertEqual(self.client.post('/api/tipos-abrigo/', {'nome': 'Praça', 'icone': '🌳'}, format='json').status_code, 201)
        self.assertEqual(self.client.post('/api/tipos-abrigo/', {'nome': 'Praça'}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/tipos-abrigo/', {'nome': 'Escola'}, format='json').status_code, 400)

    def test_admin_ve_as_areas(self):
        AreaRisco.objects.create(nome='Encosta Exemplo')
        self.entrar_como(self.admin)
        dados = self.client.get('/api/areas/').data
        self.assertEqual([a['nome'] for a in dados], ['Encosta Exemplo'])

    def test_apagar_abrigo_limpa_o_abrigo_salvo_do_morador(self):
        Usuario.objects.filter(pk=self.maria.pk).update(abrigo=self.perto)
        self.entrar_como(self.admin)
        self.client.delete(f'/api/abrigos/{self.perto.pk}/')
        self.assertIsNone(Usuario.objects.get(pk=self.maria.pk).abrigo)

    def test_banco_exige_latitude_e_longitude_juntas(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Abrigo.objects.create(nome='Meio', tipo=self.tipo, latitude='-21.7')

    def test_bairro_e_unico_na_cidade_e_aceita_ficar_sem_area(self):
        Bairro.objects.create(nome='Centro', cidade='Juiz de Fora')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Bairro.objects.create(nome='Centro', cidade='Juiz de Fora')
        self.assertIsNone(Bairro.objects.get().area)
