from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower


def normalizar_email(email):
    """O e-mail vale inteiro em minúsculas: "Maria@Gmail.com" e "maria@gmail.com" são a mesma conta."""
    return (email or '').strip().lower()


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **campos):
        usuario = self.model(email=normalizar_email(email), **campos)
        usuario.set_password(password)  # guarda só o hash, nunca a senha
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **campos):
        campos.update(is_staff=True, is_superuser=True)
        return self.create_user(email, password, **campos)

    def get_by_natural_key(self, email):
        # Usado pelo login do app e do /admin/: acha a conta digitada com qualquer caixa
        return self.get(email=normalizar_email(email))


class Usuario(AbstractUser):
    """Conta de morador ou de administrador. O login é pelo e-mail."""

    username = None
    email = models.EmailField('e-mail', unique=True)
    telefone = models.CharField(max_length=11, blank=True)
    endereco = models.CharField('endereço', max_length=255, blank=True)
    # Antigo: as ruas não são mais cadastradas. O campo fica parado, sem uso nas telas
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
    # Endereço do morador. O bairro liga a pessoa à área de risco; latitude e longitude
    # só voltam para o próprio morador (nunca aparecem para outra pessoa nem no painel)
    cep = models.CharField(max_length=8, blank=True)
    logradouro = models.CharField(max_length=150, blank=True)
    # Número na rua. Em condomínio é o número do condomínio; a casa vai no complemento
    numero = models.CharField('número', max_length=10, blank=True)
    complemento = models.CharField(max_length=60, blank=True)
    bairro = models.ForeignKey(
        'locais.Bairro', on_delete=models.SET_NULL, null=True, blank=True, related_name='moradores'
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    alertas_ativos = models.BooleanField('alertas ligados', default=True)
    # Prova do consentimento: quando foi dado e qual texto a pessoa aceitou
    consentimento_em = models.DateTimeField(null=True, blank=True)
    consentimento_texto = models.TextField(blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta(AbstractUser.Meta):
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(latitude__isnull=True, longitude__isnull=True)
                    | models.Q(latitude__isnull=False, longitude__isnull=False)
                ),
                name='usuario_lat_lng_juntas',
            ),
            # Garantia no próprio banco: nem por script ou importação nascem duas contas
            # com o mesmo e-mail escrito com maiúsculas diferentes
            models.UniqueConstraint(
                Lower('email'),
                name='usuario_email_unico_sem_caixa',
                violation_error_message='Já existe uma conta com este e-mail.',
            ),
        ]

    objects = UsuarioManager()

    def clean(self):
        super().clean()
        # O padrão do Django só passa o domínio para minúsculas. Sem isto, a conta criada
        # no /admin/ como "Ana@..." ficava assim e não entrava pelo app
        self.email = normalizar_email(self.email)

    def save(self, *args, **kwargs):
        self.email = normalizar_email(self.email)
        super().save(*args, **kwargs)

    @property
    def papel(self):
        return 'admin' if self.is_staff else 'morador'

    def __str__(self):
        return self.email


# No /admin/ as contas aparecem em duas seções. As duas são a mesma tabela de Usuario.


class Staff(Usuario):
    """Contas de ADM (ADMzão e ADMzinho)."""

    class Meta:
        proxy = True
        verbose_name = 'staff'
        verbose_name_plural = 'staffs'


class Morador(Usuario):
    """Os moradores, que no /admin/ aparecem como "Usuários": só leitura e sem dado sensível.

    O nome aparece como "Morador nº 12" para o e-mail não vazar nos títulos e caminhos
    das páginas do admin.
    """

    class Meta:
        proxy = True
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return f'Morador nº {self.pk}'
