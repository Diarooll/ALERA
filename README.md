# ALERA

**Acompanhamento Local de Emergências e Riscos Ambientais.** No lugar certo, na hora certa.

O ALERA é um projeto de alerta de chuva com o nome da sua rua, entregue no WhatsApp. Ele cruza a previsão do tempo com as áreas de risco de Juiz de Fora (MG) e avisa o morador antes da água subir ou do barranco ceder.

> **Status:** protótipo. Este repositório tem o site, uma prévia navegável do app e o começo do back-end, com contas, cadastro e login em banco de dados. O envio de alertas e os gadgets ainda não funcionam de verdade, e as telas do app e do painel ainda usam dados de exemplo.

## O problema

Fevereiro de 2026 foi o pior verão da história recente de Juiz de Fora:

- **65** mortes nas chuvas de fevereiro
- **8.854** pessoas desabrigadas ou desalojadas
- **128 mil** pessoas vivendo em áreas de risco
- **142** áreas de risco geológico mapeadas

O alerta que existe hoje vale para a cidade toda. Ele não diz qual rua ou qual encosta corre risco, e quando todo aviso parece igual, ninguém sai de casa.

As fontes desses números estão na seção de referências do site.

## Como funciona

### Fase 1: ALERA Web

Começa sem instalar nada, só com o celular:

1. **Cadastre sua rua:** o morador informa o telefone e a rua onde mora.
2. **Script + IA:** a ALERA cruza a previsão de chuva com as 142 áreas de risco da cidade.
3. **O alerta chega no WhatsApp:** com o nome da rua, o nível de risco, o que fazer e o abrigo mais próximo.

| Nível | O que significa |
| --- | --- |
| Normal | Sem chuva forte prevista. Depois de muita chuva o solo ainda pode ceder: viu rachaduras, ligue 199. |
| Atenção | Chuva prevista para hoje. Confira seu abrigo e tire o lixo da frente do bueiro. |
| Alerta | Chuva forte prevista em até 24 horas. Evite a rua e deixe documentos à mão. |
| Perigo | Risco agora. Saia de casa e vá para o abrigo. |

O app também tem missões que valem pontos, como plantar uma muda na encosta e salvar o abrigo mais próximo, e um ranking por rua. Os valores que aparecem no protótipo são simulados.

### Fase 2: Gadgets ALERA

Os gadgets entram aos poucos, área por área. O dado medido entra no mesmo alerta do WhatsApp, e os gadgets também notificam a Defesa Civil e a Secretaria de Obras.

- **Sensor ALERA:** fica na encosta e mede a umidade do solo, a chuva acumulada e a inclinação do terreno. Avisa com LEDs na rua, sirene e WhatsApp.
- **Bueiro ALERA:** um cesto segura o lixo antes da galeria, e o sensor avisa a Secretaria de Obras quando é hora de limpar.

## Como rodar

### O que precisa ter instalado

- [Python 3.12+](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/), para o banco PostgreSQL. É opcional: sem ele o projeto usa um SQLite local.
- [Git](https://git-scm.com/)

### 1. Baixar o projeto

```bash
git clone https://github.com/Diarooll/ALERA.git
cd ALERA
```

### 2. Ligar o banco (PostgreSQL no Docker)

Com o Docker Desktop aberto, na pasta raiz do projeto:

```bash
docker compose up -d
```

Sobe um PostgreSQL 17 com PostGIS em `127.0.0.1:5432`. Para desligar: `docker compose stop`.

### 3. Preparar o back-end (primeira vez)

Entre na pasta `backend`, crie o ambiente virtual e instale as dependências.

**Windows (PowerShell):**

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

O `.env` já aponta para o banco do Docker. Sem o Docker, apague a linha `DATABASE_URL` do `.env` e o projeto usa um SQLite local.

Crie as tabelas e a conta de administrador:

```bash
python manage.py migrate
python manage.py createsuperuser
```

O `createsuperuser` pede o e-mail e a senha do administrador na hora; eles não ficam no código. Contas de morador nascem na tela de cadastro.

### 4. Rodar a API

Com o ambiente virtual ativo, dentro de `backend`:

```bash
python manage.py runserver
```

A API fica em `http://127.0.0.1:8000`.

- Saúde da API: <http://127.0.0.1:8000/api/saude/>
- Django Admin: <http://127.0.0.1:8000/admin/>

### 5. Abrir o front-end

Em outro terminal, na pasta raiz do projeto:

```bash
python -m http.server 5520 --bind 127.0.0.1 --directory frontend
```

E abra no navegador:

- <http://127.0.0.1:5520/index.html>: página inicial, leva para o login
- <http://127.0.0.1:5520/site.html>: site de apresentação do projeto
- <http://127.0.0.1:5520/app/login.html>: login do app

Também dá para abrir os arquivos de `frontend/` direto no navegador ou pelo Live Server do VS Code (porta 5500). O login e o cadastro precisam da API rodando. Depois do login, a conta de administrador abre o painel e a de morador abre o app.

### Nas próximas vezes

```bash
docker compose up -d          # na raiz
cd backend
.venv\Scripts\Activate.ps1     # Windows  (no macOS/Linux: source .venv/bin/activate)
python manage.py runserver
```

E o servidor do front-end, como no passo 5.

### Testes e simulação

Dentro de `backend`, com o ambiente virtual ativo:

```bash
python manage.py test           # testes automáticos
python scripts/simular.py       # simula um dia de chuva pela API, do cadastro ao alerta de Perigo
```

A simulação usa um banco temporário e não mexe nos seus dados.

### Produção

Em produção, deixe `DJANGO_DEBUG` desligado e defina `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` e `CORS_ALLOWED_ORIGINS`. A lista completa de variáveis e as regras de segurança estão em [`backend/README.md`](backend/README.md).

## Equipe

**MonkeyNerds** · FIAP · Challenge 2026

- Daniel Souza Gomes
- Victor Santos Ferreira de Morais
- Diego Ramos Pereira Gonzalez
- Diego Alejandro Ribeiro Olalla
