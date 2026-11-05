import re

from decimal import Decimal

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from locais.models import Abrigo, Bairro

from . import geocodificacao
from .models import Usuario

# Igual ao texto da caixa de consentimento em front-end/app/login.html
TEXTO_CONSENTIMENTO = (
    'Concordo em compartilhar meu e-mail, telefone e endereço com o A.L.E.R.A para '
    'receber alertas de risco da minha rua.'
)
REGEX_CEP = re.compile(r'^\d{8}$')
# DDD + número fixo (8 dígitos) ou celular (9 + 8 dígitos), como no login.js
REGEX_TELEFONE = re.compile(r'^[1-9]{2}9?\d{8}$')


def montar_endereco(logradouro, numero, bairro, cidade):
    return f'{logradouro}, {numero}, {bairro}, {cidade}'


def achar_bairro(nome, cidade):
    """Bairro novo nasce sem área de risco: o admin completa depois."""
    bairro, _ = Bairro.objects.get_or_create(nome=nome.strip(), cidade=cidade.strip())
    return bairro


def validar_cep(valor):
    digitos = re.sub(r'\D', '', valor)
    if not REGEX_CEP.match(digitos):
        raise serializers.ValidationError('CEP inválido. Exemplo: 36010-000')
    return digitos


class CadastroSerializer(serializers.Serializer):
    """Cria só contas de morador: administradores não nascem do cadastro público."""

    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True)
    telefone = serializers.CharField()
    cep = serializers.CharField()
    logradouro = serializers.CharField(max_length=150)
    # "S/N" para casa sem número
    numero = serializers.CharField(max_length=10)
    bairro = serializers.CharField(max_length=120)
    cidade = serializers.CharField(max_length=120)
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

    def validate_cep(self, valor):
        return validar_cep(valor)

    def validate_consentimento(self, valor):
        if not valor:
            raise serializers.ValidationError('Marque a caixa para concordar e criar sua conta.')
        return valor

    def create(self, dados):
        posicao = geocodificacao.localizar(
            dados['logradouro'], dados['numero'], dados['bairro'], dados['cidade']
        )
        latitude, longitude = posicao or (None, None)

        return Usuario.objects.create_user(
            dados['email'],
            dados['senha'],
            telefone=dados['telefone'],
            endereco=montar_endereco(
                dados['logradouro'], dados['numero'], dados['bairro'], dados['cidade']
            ),
            cep=dados['cep'],
            logradouro=dados['logradouro'].strip(),
            numero=dados['numero'].strip(),
            bairro=achar_bairro(dados['bairro'], dados['cidade']),
            latitude=latitude,
            longitude=longitude,
            consentimento_em=timezone.now(),
            consentimento_texto=TEXTO_CONSENTIMENTO,
        )

    def to_representation(self, usuario):
        # Nada além do necessário: a posição da casa não volta no cadastro
        return {'email': usuario.email, 'localizado': usuario.latitude is not None}


class LoginSerializer(TokenObtainPairSerializer):
    # A mesma mensagem para e-mail ou senha errados: não revela quais e-mails têm conta
    default_error_messages = {'no_active_account': 'E-mail ou senha incorretos.'}

    def validate(self, dados):
        dados[self.username_field] = dados[self.username_field].strip().lower()
        tokens = super().validate(dados)
        return {'token': tokens['access'], 'papel': self.user.papel}


class MeuPerfilSerializer(serializers.ModelSerializer):
    papel = serializers.CharField(read_only=True)
    # No GET volta o nome do bairro e da cidade; no PATCH chegam como texto
    bairro = serializers.CharField(max_length=120, required=False)
    cidade = serializers.CharField(max_length=120, required=False)
    cep = serializers.CharField(required=False)
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal('-90'),
        max_value=Decimal('90'),
        required=False,
        allow_null=True,
        coerce_to_string=False,
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal('-180'),
        max_value=Decimal('180'),
        required=False,
        allow_null=True,
        coerce_to_string=False,
    )
    abrigo = serializers.PrimaryKeyRelatedField(
        queryset=Abrigo.objects.all(), required=False, allow_null=True
    )
    area = serializers.SerializerMethodField()
    localizado = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'email',
            'papel',
            'telefone',
            'endereco',
            'cep',
            'logradouro',
            'numero',
            'bairro',
            'cidade',
            'latitude',
            'longitude',
            'abrigo',
            'alertas_ativos',
            'area',
            'localizado',
        ]
        read_only_fields = ['email', 'telefone', 'endereco']

    def to_representation(self, usuario):
        dados = super().to_representation(usuario)
        dados['bairro'] = usuario.bairro.nome if usuario.bairro else ''
        dados['cidade'] = usuario.bairro.cidade if usuario.bairro else ''
        return dados

    def get_area(self, usuario):
        area = usuario.bairro.area if usuario.bairro else None
        return {'nome': area.nome, 'nivel': area.nivel} if area else None

    def get_localizado(self, usuario):
        return usuario.latitude is not None

    def validate_cep(self, valor):
        return validar_cep(valor)

    def validate_abrigo(self, abrigo):
        if abrigo and abrigo.situacao == Abrigo.Situacao.FECHADO:
            raise serializers.ValidationError('Este abrigo está fechado e não pode ser salvo.')
        return abrigo

    def validate(self, dados):
        # Latitude e longitude andam juntas: ou as duas, ou nenhuma
        if ('latitude' in dados) != ('longitude' in dados):
            raise serializers.ValidationError('Envie latitude e longitude juntas.')
        if (dados.get('latitude') is None) != (dados.get('longitude') is None):
            raise serializers.ValidationError('Envie latitude e longitude juntas.')
        return dados

    def update(self, usuario, dados):
        nome_bairro = dados.pop('bairro', None)
        cidade = dados.pop('cidade', None)
        posicao_enviada = 'latitude' in dados

        endereco_mudou = False
        if nome_bairro is not None or cidade is not None:
            atual = usuario.bairro
            nome_bairro = nome_bairro or (atual.nome if atual else '')
            cidade = cidade or (atual.cidade if atual else '')
            usuario.bairro = achar_bairro(nome_bairro, cidade)
            # O formulário sempre envia o bairro: só conta como mudança se for outro
            endereco_mudou = usuario.bairro != atual

        for campo in ('cep', 'logradouro', 'numero'):
            if campo in dados and dados[campo] != getattr(usuario, campo):
                endereco_mudou = True

        for campo, valor in dados.items():
            setattr(usuario, campo, valor)

        if endereco_mudou:
            usuario.endereco = montar_endereco(
                usuario.logradouro,
                usuario.numero,
                usuario.bairro.nome if usuario.bairro else '',
                usuario.bairro.cidade if usuario.bairro else '',
            )
            # Se a pessoa já marcou o ponto no mapa, vale o que ela marcou
            if not posicao_enviada:
                posicao = geocodificacao.localizar(
                    usuario.logradouro,
                    usuario.numero,
                    usuario.bairro.nome if usuario.bairro else '',
                    usuario.bairro.cidade if usuario.bairro else '',
                )
                usuario.latitude, usuario.longitude = posicao or (None, None)

        usuario.save()
        return usuario
