import re

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Usuario

# Igual ao texto da caixa de consentimento em front-end/app/login.html
TEXTO_CONSENTIMENTO = (
    'Concordo em compartilhar meu e-mail, telefone e endereço com o A.L.E.R.A para '
    'receber alertas de risco da minha rua.'
)
# DDD + número fixo (8 dígitos) ou celular (9 + 8 dígitos), como no login.js
REGEX_TELEFONE = re.compile(r'^[1-9]{2}9?\d{8}$')


class CadastroSerializer(serializers.Serializer):
    """Cria só contas de morador: administradores não nascem do cadastro público."""

    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True)
    telefone = serializers.CharField()
    endereco = serializers.CharField(min_length=8, max_length=255)
    consentimento = serializers.BooleanField(write_only=True)

    def validate_email(self, valor):
        valor = valor.strip().lower()
        if Usuario.objects.filter(email=valor).exists():
            raise serializers.ValidationError('Este e-mail já tem uma conta.')
        return valor

    def validate_senha(self, valor):
        validate_password(valor)
        return valor

    def validate_telefone(self, valor):
        digitos = re.sub(r'\D', '', valor)
        if not REGEX_TELEFONE.match(digitos):
            raise serializers.ValidationError('Telefone inválido. Exemplo: (32) 99999-0000')
        return digitos

    def validate_consentimento(self, valor):
        if not valor:
            raise serializers.ValidationError('Marque a caixa para concordar e criar sua conta.')
        return valor

    def create(self, dados):
        return Usuario.objects.create_user(
            dados['email'],
            dados['senha'],
            telefone=dados['telefone'],
            endereco=dados['endereco'],
            consentimento_em=timezone.now(),
            consentimento_texto=TEXTO_CONSENTIMENTO,
        )


class LoginSerializer(TokenObtainPairSerializer):
    # A mesma mensagem para e-mail ou senha errados: não revela quais e-mails têm conta
    default_error_messages = {'no_active_account': 'E-mail ou senha incorretos.'}

    def validate(self, dados):
        dados[self.username_field] = dados[self.username_field].strip().lower()
        tokens = super().validate(dados)
        return {'token': tokens['access'], 'papel': self.user.papel}


class MeuPerfilSerializer(serializers.ModelSerializer):
    papel = serializers.CharField(read_only=True)

    class Meta:
        model = Usuario
        fields = ['email', 'papel', 'telefone', 'endereco']
