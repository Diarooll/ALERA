from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **campos):
        usuario = self.model(email=email.strip().lower(), **campos)
        usuario.set_password(password)  # guarda só o hash, nunca a senha
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **campos):
        campos.update(is_staff=True, is_superuser=True)
        return self.create_user(email, password, **campos)


class Usuario(AbstractUser):
    """Conta de morador ou de administrador. O login é pelo e-mail."""

    username = None
    email = models.EmailField('e-mail', unique=True)
    telefone = models.CharField(max_length=11, blank=True)
    endereco = models.CharField('endereço', max_length=255, blank=True)
    # Ficam vazios em contas da Defesa Civil, que não moram em uma rua do sistema
    rua = models.ForeignKey(
        'locais.Rua', on_delete=models.PROTECT, null=True, blank=True, related_name='moradores'
    )
    abrigo = models.ForeignKey(
        'locais.Abrigo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moradores',
        verbose_name='abrigo salvo',
    )
    alertas_ativos = models.BooleanField('alertas ligados', default=True)
    # Prova do consentimento: quando foi dado e qual texto a pessoa aceitou
    consentimento_em = models.DateTimeField(null=True, blank=True)
    consentimento_texto = models.TextField(blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    @property
    def papel(self):
        return 'admin' if self.is_staff else 'morador'

    def __str__(self):
        return self.email
