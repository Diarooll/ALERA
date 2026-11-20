"""Simula o uso comum do ALERA pela API, do mesmo jeito que o site faz.

Como rodar (de dentro de backend/):

    .venv\\Scripts\\python.exe scripts\\simular.py

O que acontece:
1. Cria um banco temporário numa pasta descartável. O seu db.sqlite3 não é tocado.
2. Cria uma conta de staff da Defesa Civil com senha aleatória (só existe nessa pasta).
3. Sobe o servidor numa porta livre, sem consultar o mapa de verdade (ver servidor.py).
4. Faz a história de um dia de chuva: o admin prepara abrigos e área de risco,
   uma moradora se cadastra e marca a casa, o admin emite Alerta e depois Perigo,
   e a moradora vê o nível mudar. No meio, confere as regras de sessão e segurança.
5. Mostra cada passo com ✔ ou ✘, derruba o servidor e apaga a pasta.

Sai com código 1 se algum passo falhar, então dá para usar em CI.
Só usa a biblioteca padrão do Python.
"""

import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

PASTA_BACKEND = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

# Pontos perto da Rua Halfeld, centro de Juiz de Fora. A casa fica dentro da área.
CENTRO_DA_AREA = (-21.7615, -43.3495)
CASA = (-21.7620, -43.3490)
ABRIGO_ABERTO = (-21.7600, -43.3480)
ABRIGO_FECHADO = (-21.7630, -43.3505)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')  # para o ✔ e o ✘ aparecerem no Windows


# ---------- Placar ----------

falhas = []


def titulo(texto):
    print(f'\n== {texto} ==')


def passo(descricao, deu_certo, detalhe=''):
    """Marca um passo. Em caso de falha, mostra o que o servidor respondeu."""
    print(f'  {"✔" if deu_certo else "✘"} {descricao}')
    if not deu_certo:
        falhas.append(descricao)
        if detalhe:
            print(f'      resposta: {str(detalhe)[:300]}')
    return deu_certo


# ---------- Conversa com a API ----------


class Pessoa:
    """Alguém usando o site: guarda o token e a renovação como o api.js faz."""

    def __init__(self, base, nome):
        self.base = base
        self.nome = nome
        self.token = None
        self.renovacao = None

    def pedir(self, metodo, rota, corpo=None, com_token=True):
        cabecalhos = {'Content-Type': 'application/json'}
        if com_token and self.token:
            cabecalhos['Authorization'] = f'Bearer {self.token}'
        dados = None if corpo is None else json.dumps(corpo).encode()
        pedido = urllib.request.Request(f'{self.base}{rota}', data=dados, headers=cabecalhos, method=metodo)
        try:
            with urllib.request.urlopen(pedido, timeout=15) as resposta:
                texto = resposta.read().decode()
                return resposta.status, (json.loads(texto) if texto else None)
        except urllib.error.HTTPError as erro:
            texto = erro.read().decode()
            try:
                return erro.code, json.loads(texto)
            except ValueError:
                return erro.code, texto

    def entrar(self, email, senha):
        status, dados = self.pedir('POST', '/auth/login/', {'email': email, 'password': senha}, com_token=False)
        if status == 200:
            self.token = dados['token']
            self.renovacao = dados['renovacao']
        return status, dados

    def renovar(self):
        status, dados = self.pedir('POST', '/auth/renovar/', {'renovacao': self.renovacao}, com_token=False)
        if status == 200:
            self.token = dados['token']
            self.renovacao = dados['renovacao']
        return status, dados

    def sair(self):
        status, _ = self.pedir('POST', '/auth/sair/', {'renovacao': self.renovacao}, com_token=False)
        return status


# ---------- A história ----------


def admin_prepara_a_cidade(admin, email, senha):
    titulo('Admin (Defesa Civil) prepara a cidade')

    status, dados = admin.entrar(email, senha)
    passo('Entra no painel', status == 200 and dados.get('papel') == 'admin', dados)

    status, perfil = admin.pedir('GET', '/me/')
    passo('O servidor reconhece a conta como admin', status == 200 and perfil.get('papel') == 'admin', perfil)

    status, tipos = admin.pedir('GET', '/tipos-abrigo/')
    passo('Lê os tipos de abrigo', status == 200 and len(tipos) > 0, tipos)
    tipo = tipos[0]['id'] if tipos else None

    abrigos = {}
    for chave, nome, (lat, lon), situacao in [
        ('aberto', 'Escola Municipal do Centro [SIMULAÇÃO]', ABRIGO_ABERTO, 'aberto'),
        ('fechado', 'Ginásio da Encosta [SIMULAÇÃO]', ABRIGO_FECHADO, 'fechado'),
    ]:
        status, abrigo = admin.pedir('POST', '/abrigos/', {
            'nome': nome,
            'tipo': tipo,
            'referencia': 'Entrada pelo portão lateral',
            'situacao': situacao,
            'latitude': lat,
            'longitude': lon,
            'capacidade': 120,
        })
        passo(f'Cadastra o abrigo {situacao}: {nome}', status == 201, abrigo)
        abrigos[chave] = abrigo.get('id') if status == 201 else None

    lat, lon = CENTRO_DA_AREA
    status, area = admin.pedir('POST', '/areas/', {
        'nome': 'Encosta do Centro [SIMULAÇÃO]',
        'circulos': [{'latitude': lat, 'longitude': lon, 'raio_m': 400}],
    })
    passo('Desenha a área de risco com uma bolinha de 400 m', status == 201 and area.get('nivel') == 'normal', area)
    area_id = area.get('id') if status == 201 else None

    return abrigos, area_id


def moradora_chega(base, email, senha):
    titulo('Moradora se cadastra e configura o app')
    moradora = Pessoa(base, 'moradora')

    status, dados = moradora.pedir('POST', '/auth/cadastro/', {
        'email': email,
        'senha': senha,
        'telefone': '(32) 99999-0000',
        'cep': '36010-001',
        'logradouro': 'Rua Halfeld',
        'numero': '414',
        'complemento': 'Fundos',
        'bairro': 'Centro',
        'cidade': 'Juiz de Fora',
        'consentimento': True,
    }, com_token=False)
    passo('Cria a conta (o mapa não achou a casa, como acontece de verdade às vezes)',
          status == 201 and dados.get('localizado') is False, dados)

    status, _ = moradora.pedir('POST', '/auth/cadastro/', {
        'email': email.upper(), 'senha': senha, 'telefone': '32999990000', 'cep': '36010001',
        'logradouro': 'Rua Halfeld', 'numero': '1', 'bairro': 'Centro', 'cidade': 'Juiz de Fora',
        'consentimento': True,
    }, com_token=False)
    passo('Não deixa criar outra conta com o mesmo e-mail em maiúsculas', status == 400)

    status, _ = moradora.entrar(email, 'senha-errada-123')
    passo('Senha errada é recusada', status == 401)

    status, dados = moradora.entrar(email.upper(), senha)
    passo('Entra digitando o e-mail em maiúsculas', status == 200 and dados.get('papel') == 'morador', dados)

    status, perfil = moradora.pedir('GET', '/me/')
    passo('Antes de marcar a casa, o app não sabe a área', status == 200 and perfil.get('area') is None, perfil)

    lat, lon = CASA
    status, perfil = moradora.pedir('PATCH', '/me/', {'latitude': lat, 'longitude': lon})
    passo('Marca a casa no mapa ("Meus dados")', status == 200 and perfil.get('localizado') is True, perfil)

    status, perfil = moradora.pedir('GET', '/me/')
    area = (perfil or {}).get('area') or {}
    passo('Agora o app mostra a área dela, em nível Normal',
          status == 200 and area.get('nome') == 'Encosta do Centro [SIMULAÇÃO]' and area.get('nivel') == 'normal', perfil)

    status, lista = moradora.pedir('GET', '/abrigos/')
    com_distancia = status == 200 and all(a.get('distancia_m') is not None for a in lista)
    passo('Vê os abrigos com distância e tempo a pé a partir da casa', com_distancia, lista)

    return moradora


def moradora_escolhe_abrigo(moradora, abrigos):
    titulo('Moradora escolhe o abrigo')

    status, resposta = moradora.pedir('PATCH', '/me/', {'abrigo': abrigos['fechado']})
    passo('Não consegue salvar um abrigo fechado', status == 400 and 'abrigo' in (resposta or {}), resposta)

    status, perfil = moradora.pedir('PATCH', '/me/', {'abrigo': abrigos['aberto']})
    passo('Salva o abrigo aberto mais perto', status == 200 and perfil.get('abrigo') == abrigos['aberto'], perfil)

    status, resposta = moradora.pedir('PATCH', '/me/', {'logradouro': ''})
    passo('Não consegue apagar a rua (o erro vem no campo certo)', status == 400 and 'logradouro' in (resposta or {}), resposta)


def chuva_aperta(admin, moradora, area_id):
    for nivel, mensagem in [
        ('alerta', 'Chuva forte prevista em até 24 horas. Evite a rua e deixe documentos à mão.'),
        ('perigo', 'Risco agora. Saia de casa e vá para o abrigo.'),
    ]:
        titulo(f'A chuva aperta: admin emite {nivel.upper()}')

        status, gravados = admin.pedir('POST', '/alertas/', {'areas': [area_id], 'nivel': nivel, 'mensagem': mensagem})
        passo(f'Admin emite {nivel} para a Encosta do Centro', status == 201 and len(gravados) == 1, gravados)

        # O app confere o nível a cada minuto: aqui é a próxima conferência
        status, perfil = moradora.pedir('GET', '/me/')
        area = (perfil or {}).get('area') or {}
        passo(f'Na conferência seguinte, o app da moradora mostra {nivel}', area.get('nivel') == nivel, perfil)
        passo('E mostra a orientação que o admin escreveu', area.get('orientacao') == mensagem, perfil)

    status, historico = admin.pedir('GET', '/alertas/')
    niveis = [h.get('nivel_novo') for h in historico] if status == 200 else []
    passo('O histórico do painel tem os dois alertas, do mais novo para o mais velho',
          niveis[:2] == ['perigo', 'alerta'], historico)


def regras_de_seguranca(moradora):
    titulo('Regras de segurança')

    status, _ = moradora.pedir('POST', '/alertas/', {'areas': [1], 'nivel': 'normal'})
    passo('Moradora não consegue emitir alerta', status == 403)

    status, _ = moradora.pedir('POST', '/abrigos/', {'nome': 'Abrigo falso'})
    passo('Moradora não consegue criar abrigo', status == 403)

    intruso = Pessoa(moradora.base, 'intruso')
    status, _ = intruso.pedir('GET', '/me/')
    passo('Sem login, a API não mostra dados', status == 401)


def sessao_que_nao_cai(pessoa):
    titulo(f'Sessão da {pessoa.nome}: renovação e saída')

    renovacao_velha = pessoa.renovacao
    status, _ = pessoa.renovar()
    passo('O site renova o login sozinho (é o que impede o login de cair)', status == 200)

    status, perfil = pessoa.pedir('GET', '/me/')
    passo('O token novo funciona', status == 200, perfil)

    status, _ = pessoa.pedir('POST', '/auth/renovar/', {'renovacao': renovacao_velha}, com_token=False)
    passo('A renovação velha não vale mais (rodízio)', status == 401)

    status = pessoa.sair()
    passo('Clica em Sair', status in (200, 204))

    status, _ = pessoa.renovar()
    passo('Depois de sair, não dá para renovar', status == 401)


# ---------- Preparação: banco e servidor descartáveis ----------


def porta_livre():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def rodar_manage(ambiente, *argumentos):
    resultado = subprocess.run(
        [PYTHON, 'manage.py', *argumentos], cwd=PASTA_BACKEND, env=ambiente,
        capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        print(resultado.stdout, resultado.stderr)
        raise SystemExit(f'Falhou: manage.py {" ".join(argumentos)}')


def esperar_servidor(base, servidor):
    for _ in range(60):
        if servidor.poll() is not None:
            raise SystemExit('O servidor não subiu. Rode o simulador de novo para ver o erro.')
        try:
            with urllib.request.urlopen(f'{base}/saude/', timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise SystemExit('O servidor não respondeu em 30 segundos.')


def principal():
    pasta = Path(tempfile.mkdtemp(prefix='alera-simulacao-'))
    porta = porta_livre()
    base = f'http://127.0.0.1:{porta}/api'

    # Variáveis do ambiente valem mais que o backend/.env, então o banco é o temporário
    ambiente = {
        **os.environ,
        'DJANGO_DEBUG': 'true',
        'DJANGO_SECRET_KEY': secrets.token_urlsafe(50),
        'DATABASE_URL': f'sqlite:///{(pasta / "simulacao.sqlite3").as_posix()}',
        'PYTHONIOENCODING': 'utf-8',
    }

    email_admin = 'defesacivil@simulacao.alera'
    senha_admin = secrets.token_urlsafe(16)
    email_moradora = 'Moradora.Simulada@simulacao.alera'
    senha_moradora = secrets.token_urlsafe(16)

    servidor = None
    try:
        print(f'Preparando banco temporário em {pasta}')
        rodar_manage(ambiente, 'migrate', '--noinput')
        rodar_manage(
            {**ambiente, 'SIM_EMAIL': email_admin, 'SIM_SENHA': senha_admin},
            'shell', '-c',
            'import os; from usuarios.models import Usuario; '
            "Usuario.objects.create_user(os.environ['SIM_EMAIL'], os.environ['SIM_SENHA'], is_staff=True)",
        )

        print(f'Subindo o servidor em {base}')
        servidor = subprocess.Popen(
            [PYTHON, str(Path(__file__).with_name('servidor.py')), str(porta)],
            cwd=PASTA_BACKEND, env=ambiente, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        esperar_servidor(base, servidor)

        admin = Pessoa(base, 'admin')
        abrigos, area_id = admin_prepara_a_cidade(admin, email_admin, senha_admin)
        if None in abrigos.values() or area_id is None:
            raise SystemExit('A preparação do admin falhou; o resto da história depende dela.')

        moradora = moradora_chega(base, email_moradora, senha_moradora)
        moradora_escolhe_abrigo(moradora, abrigos)
        chuva_aperta(admin, moradora, area_id)
        regras_de_seguranca(moradora)
        sessao_que_nao_cai(moradora)
        sessao_que_nao_cai(admin)
    finally:
        if servidor:
            servidor.terminate()
            servidor.wait(timeout=10)
        shutil.rmtree(pasta, ignore_errors=True)

    print()
    if falhas:
        print(f'✘ {len(falhas)} passo(s) falharam:')
        for descricao in falhas:
            print(f'  - {descricao}')
        sys.exit(1)
    print('✔ Tudo certo: o admin e a moradora fizeram o caminho inteiro.')


if __name__ == '__main__':
    principal()
