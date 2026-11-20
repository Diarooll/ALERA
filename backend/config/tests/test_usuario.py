from django.contrib.auth import get_user_model
from django.test import TestCase


class UsuarioTests(TestCase):
    def test_projeto_usa_o_usuario_do_alera(self):
        usuario = get_user_model().objects.create_user('teste@exemplo.com', 's3nh4-de-teste')

        self.assertEqual(usuario._meta.label, 'usuarios.Usuario')
        self.assertTrue(usuario.check_password('s3nh4-de-teste'))
