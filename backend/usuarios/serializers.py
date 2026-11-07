import re

from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from locais import servicos as servicos_locais
from locais.models import Abrigo, Bairro
from locais.serializers import campo_latitude, campo_longitude

from . import geocodificacao
from .models import Usuario, normalizar_email

# Igual ao texto da caixa de consentimento em front-end/app/login.html
TEXTO_CONSENTIMENTO = (
    'Concordo em compartilhar meu e-mail, telefone e endereço com o A.L.E.R.A para '
    'receber alertas de risco da minha rua.'
)
REGEX_CEP = re.compile(r'^\d{8}$')
# DDD + número fixo (8 dígitos) ou celular (9 + 8 dígitos), como no login.js
REGEX_TELEFONE = re.compile(r'^[1-9]{2}9?\d{8}$')
EMAIL_REPETIDO = 'Este e-mail já tem uma conta.'


def normalizar_telefone(valor):
    """Só os dígitos, com DDD. O "+55" do começo sai, como na máscara do login.js."""
    return re.sub(r'\D', '', re.sub(r'^\s*\+55', '', valor))


def montar_endereco(logradouro, numero, bairro, cidade, complemento=''):
    partes = [logradouro, numero, complemento, bairro, cidade]
    return ', '.join(p for p in partes if p)


def achar_bairro(nome, cidade):
    """Bairro novo nasce sem área de risco: o admin completa depois.

    "Centro" e "centro" são o mesmo bairro. Sem isso nascia outro bairro, e no perfil
    mudar só a maiúscula consultava o mapa de novo e trocava o ponto marcado pela pessoa.
    """
    nome, cidade = ' '.join(nome.split()), ' '.join(cidade.split())
    achado = Bairro.objects.filter(nome__iexact=nome, cidade__iexact=cidade).first()
    return achado or Bairro.objects.get_or_create(nome=nome, cidade=cidade)[0]


def validar_cep(valor):
    digitos = re.sub(r'\D', '', valor)
    if not REGEX_CEP.match(digitos):
        raise serializers.ValidationError('CEP inválido. Exemplo: 36010-000')
    return digitos


class CadastroSerializer(serializers.Serializer):
    """Cria só contas de morador: administradores não nascem do cadastro público."""

    # 254 é o tamanho da coluna: maior que isso dava erro 500 no PostgreSQL
    email = serializers.EmailField(max_length=254)
    senha = serializers.CharField(write_only=True)
    telefone = serializers.CharField()
    cep = serializers.CharField()
    logradouro = serializers.CharField(max_length=150)
    # "S/N" para casa sem número
    numero = serializers.CharField(max_length=10)
    # Casa ou apartamento dentro do condomínio. Não entra na busca do mapa
    complemento = serializers.CharField(max_length=60, required=False, allow_blank=True, default='')
    bairro = serializers.CharField(max_length=120)
    cidade = serializers.CharField(max_length=120)
    consentimento = serializers.BooleanField(write_only=True)

    def validate_email(self, valor):
        valor = normalizar_email(valor)
        if Usuario.objects.filter(email__iexact=valor).exists():
            raise serializers.ValidationError(EMAIL_REPETIDO)
        return valor

    def validate_senha(self, valor):
        validate_password(valor)
        return valor

    def validate_telefone(self, valor):
        digitos = normalizar_telefone(valor)
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
            dados['logradouro'], dados['numero'], dados['bairro'], dados['cidade'], dados['cep']
        )
        latitude, longitude = posicao or (None, None)

        try:
            # O atomic isola o erro: o e-mail repetido não estraga o resto da transação
            with transaction.atomic():
                return Usuario.objects.create_user(
                    dados['email'],
                    dados['senha'],
                    telefone=dados['telefone'],
                    endereco=montar_endereco(
                        dados['logradouro'],
                        dados['numero'],
                        dados['bairro'],
                        dados['cidade'],
                        dados['complemento'],
                    ),
                    cep=dados['cep'],
                    logradouro=dados['logradouro'].strip(),
                    numero=dados['numero'].strip(),
                    complemento=dados['complemento'].strip(),
                    bairro=achar_bairro(dados['bairro'], dados['cidade']),
                    latitude=latitude,
                    longitude=longitude,
                    consentimento_em=timezone.now(),
                    consentimento_texto=TEXTO_CONSENTIMENTO,
                )
        except IntegrityError:
            # Outro cadastro com o mesmo e-mail terminou enquanto este buscava a casa no mapa
            if Usuario.objects.filter(email__iexact=dados['email']).exists():
                raise serializers.ValidationError({'email': [EMAIL_REPETIDO]})
            raise

    def to_representation(self, usuario):
        # Nada além do necessário: a posição da casa não volta no cadastro
        return {'email': usuario.email, 'localizado': usuario.latitude is not None}


class LoginSerializer(TokenObtainPairSerializer):
    # A mesma mensagem para e-mail ou senha errados: não revela quais e-mails têm conta
    default_error_messages = {'no_active_account': 'E-mail ou senha incorretos.'}
    # Conta de administrador emite alerta para a cidade inteira: a sessão dela acaba depois de
    # 12 horas sem uso (um turno). A do morador, 30 dias (REFRESH_TOKEN_LIFETIME no settings.py).
    # Os dois prazos andam junto com o uso: cada renovação conta o prazo de novo
    SESSAO_ADMIN = timezone.timedelta(hours=12)

    @classmethod
    def prazo_da_sessao(cls, usuario):
        return cls.SESSAO_ADMIN if usuario.is_staff else cls.token_class.lifetime

    @classmethod
    def get_token(cls, usuario):
        token = super().get_token(usuario)
        token.set_exp(lifetime=cls.prazo_da_sessao(usuario))
        return token

    def validate(self, dados):
        dados[self.username_field] = dados[self.username_field].strip().lower()
        tokens = super().validate(dados)
        # "token" vence rápido; "renovacao" troca por um novo sem pedir a senha (ver /auth/renovar/)
        return {'token': tokens['access'], 'renovacao': tokens['refresh'], 'papel': self.user.papel}


class MeuPerfilSerializer(serializers.ModelSerializer):
    papel = serializers.CharField(read_only=True)
    # No GET volta o nome do bairro e da cidade; no PATCH chegam como texto
    bairro = serializers.CharField(max_length=120, required=False)
    cidade = serializers.CharField(max_length=120, required=False)
    cep = serializers.CharField(required=False)
    latitude = campo_latitude(required=False, allow_null=True)
    longitude = campo_longitude(required=False, allow_null=True)
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
            'complemento',
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
        # Como no cadastro: a rua e o número não podem ser apagados ("S/N" para casa sem número)
        extra_kwargs = {'logradouro': {'allow_blank': False}, 'numero': {'allow_blank': False}}

    def to_representation(self, usuario):
        dados = super().to_representation(usuario)
        dados['bairro'] = usuario.bairro.nome if usuario.bairro else ''
        dados['cidade'] = usuario.bairro.cidade if usuario.bairro else ''
        return dados

    def get_area(self, usuario):
        # Vale a posição da casa: a área mais grave entre as bolinhas que contêm a casa.
        # O morador recebe só o nome, o nível e a orientação, nunca o desenho das bolinhas
        area = servicos_locais.area_mais_grave(usuario.latitude, usuario.longitude)
        if not area:
            return None
        return {'nome': area.nome, 'nivel': area.nivel, 'orientacao': area.orientacao}

    def get_localizado(self, usuario):
        return usuario.latitude is not None

    def validate_cep(self, valor):
        return validar_cep(valor)

    def validate_abrigo(self, abrigo):
        if abrigo and abrigo.situacao == Abrigo.Situacao.FECHADO:
            raise serializers.ValidationError('Este abrigo está fechado e não pode ser salvo.')
        return abrigo

    def validate(self, dados):
        # Latitude e longitude andam juntas: ou as duas, ou nenhuma.
        # O erro vai no campo, no mesmo formato {campo: [mensagem]} dos outros
        if ('latitude' in dados) != ('longitude' in dados) or (
            (dados.get('latitude') is None) != (dados.get('longitude') is None)
        ):
            raise serializers.ValidationError({'latitude': ['Envie latitude e longitude juntas.']})
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
        # O complemento (casa ou apto) muda o endereço escrito, mas não o ponto no mapa
        complemento_mudou = 'complemento' in dados and dados['complemento'] != usuario.complemento

        for campo, valor in dados.items():
            setattr(usuario, campo, valor)

        nome_do_bairro = usuario.bairro.nome if usuario.bairro else ''
        nome_da_cidade = usuario.bairro.cidade if usuario.bairro else ''

        if endereco_mudou or complemento_mudou:
            usuario.endereco = montar_endereco(
                usuario.logradouro, usuario.numero, nome_do_bairro, nome_da_cidade, usuario.complemento
            )

        # Se a pessoa já marcou o ponto no mapa, vale o que ela marcou
        if endereco_mudou and not posicao_enviada:
            posicao = geocodificacao.localizar(
                usuario.logradouro, usuario.numero, nome_do_bairro, nome_da_cidade, usuario.cep
            )
            usuario.latitude, usuario.longitude = posicao or (None, None)

        usuario.save()
        return usuario
