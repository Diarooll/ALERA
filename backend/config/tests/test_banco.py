from django.test import SimpleTestCase

from .base import settings_de_producao

SUPABASE_DIRETO = 'postgres://alera:senha@db.exemplo.supabase.co:5432/postgres'
SUPABASE_TRANSACAO = 'postgres://alera:senha@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'
DOCKER = 'postgres://alera:alera-local@127.0.0.1:5432/alera'


def banco(**ambiente):
    return settings_de_producao(**ambiente).DATABASES['default']


class ConexaoComOBancoTests(SimpleTestCase):
    def test_producao_exige_ssl(self):
        self.assertEqual(banco(DATABASE_URL=SUPABASE_DIRETO)['OPTIONS']['sslmode'], 'require')

    def test_ssl_escrito_no_endereco_vale_mais(self):
        conexao = banco(DATABASE_URL=SUPABASE_DIRETO + '?sslmode=verify-full')

        self.assertEqual(conexao['OPTIONS']['sslmode'], 'verify-full')

    def test_docker_no_desenvolvimento_conecta_sem_ssl(self):
        # O PostgreSQL do docker-compose.yml não tem certificado
        conexao = banco(DJANGO_DEBUG='true', DATABASE_URL=DOCKER)

        self.assertNotIn('sslmode', conexao['OPTIONS'])

    def test_conexao_direta_guarda_a_conexao_e_confere_antes_de_reusar(self):
        conexao = banco(DATABASE_URL=SUPABASE_DIRETO)

        self.assertEqual(conexao['CONN_MAX_AGE'], 60)
        self.assertTrue(conexao['CONN_HEALTH_CHECKS'])
        self.assertFalse(conexao.get('DISABLE_SERVER_SIDE_CURSORS', False))

    def test_pooler_de_transacao_nao_depende_da_conexao_anterior(self):
        conexao = banco(DATABASE_URL=SUPABASE_TRANSACAO)

        self.assertEqual(conexao['CONN_MAX_AGE'], 0)
        self.assertTrue(conexao['DISABLE_SERVER_SIDE_CURSORS'])
        self.assertIsNone(conexao['OPTIONS']['prepare_threshold'])
        self.assertEqual(conexao['OPTIONS']['sslmode'], 'require')

    def test_desiste_se_o_banco_nao_responder_e_se_identifica(self):
        opcoes = banco(DATABASE_URL=SUPABASE_DIRETO)['OPTIONS']

        self.assertEqual(opcoes['connect_timeout'], 10)
        self.assertEqual(opcoes['application_name'], 'alera-api')

    def test_sqlite_fica_como_esta(self):
        conexao = banco(DATABASE_URL='sqlite:///teste.sqlite3')

        self.assertEqual(conexao['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(conexao.get('OPTIONS', {}), {})
