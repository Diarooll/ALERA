from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    """Usuário do ALERA.

    Ainda não tem campos próprios. Existe desde a primeira migração porque trocar
    o modelo de usuário depois, com o banco já criado, é bem mais difícil.
    """
