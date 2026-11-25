# ALERA: back-end

API em Django e Django REST Framework. Já existem as contas, o login, o cadastro e as tabelas do projeto. As rotas de alerta, missões e ranking ainda não foram feitas.

## Pastas

| Pasta | Função |
| --- | --- |
| `config/` | Configurações e rotas principais |
| `usuarios/` | Moradores e login |
| `locais/` | Ruas, áreas de risco e abrigos |
| `alertas/` | Previsões, regras de risco e histórico de níveis |
| `missoes/` | Missões, pontos e ranking |

## Como rodar no Windows (PowerShell)

Dentro da pasta `backend`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Ligue o banco (PostgreSQL no Docker). Precisa do [Docker Desktop](https://www.docker.com/products/docker-desktop/) aberto. Na pasta raiz do projeto:

```powershell
docker compose up -d
```

Copie `backend/.env.example` para `backend/.env`. Ele já aponta o `DATABASE_URL` para esse banco. Sem o Docker, apague a linha do `DATABASE_URL` no `.env` e o projeto usa um SQLite local. Depois:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ou com o uvicorn (reinicia sozinho ao salvar):

```powershell
uvicorn config.asgi:application --reload --port 8000
```

- Saúde da API: <http://127.0.0.1:8000/api/saude/>
- Django Admin: <http://127.0.0.1:8000/admin/>

Para rodar os testes:

```powershell
python manage.py test
```

## Simulação de uso

`scripts/simular.py` conta a história de um dia de chuva pela API, do jeito que o site faz. O admin cadastra abrigos e desenha a área de risco. Uma moradora se cadastra, marca a casa e salva o abrigo. O admin emite Alerta e depois Perigo, e o app da moradora mostra cada mudança. No caminho, o script também confere as permissões e a renovação do login.

```powershell
.venv\Scripts\python.exe scripts\simular.py
```

- Usa um banco temporário e um servidor numa porta livre, e apaga tudo no fim: o `db.sqlite3` não é tocado.
- Não consulta o mapa de verdade (Nominatim). A moradora marca a casa pelo "Meus dados".
- Mostra cada passo com ✔ ou ✘ e sai com código 1 se algum falhar.

## Variáveis de ambiente

| Variável | Obrigatória | Uso |
| --- | --- | --- |
| `DJANGO_DEBUG` | Não | `true` só em desenvolvimento |
| `DJANGO_SECRET_KEY` | Fora do modo de desenvolvimento | Chave secreta do Django. Sem ela, no desenvolvimento, cada computador cria a sua em `backend/.chave-local`, que não vai para o Git |
| `DATABASE_URL` | Fora do modo de desenvolvimento | Conexão com o PostgreSQL, como `postgres://usuario:senha@host:5432/alera` |
| `DJANGO_ALLOWED_HOSTS` | Fora do modo de desenvolvimento | Domínios da API, separados por vírgula |
| `CORS_ALLOWED_ORIGINS` | Quando o front-end chamar a API | Endereços do front-end, separados por vírgula, como `http://127.0.0.1:5500` |
| `DJANGO_NUM_PROXIES` | Quando houver proxy na frente da API | Quantos proxies de confiança repassam o IP de quem acessa. Padrão `0`. Na hospedagem atrás de um proxy, normalmente `1`; sem isso, o limite de tentativas conta todo mundo como um só IP |
| `DJANGO_ATRAS_DA_CLOUDFLARE` | Quando a Cloudflare estiver na frente | `true` para o limite de tentativas contar pelo IP do visitante, que a Cloudflare manda no cabeçalho `CF-Connecting-IP`. Padrão `false` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Raramente | Endereços com `https://` de onde o navegador pode enviar formulário ao `/admin/`, separados por vírgula. Só é preciso se o endereço visto no navegador não chegar igual ao Django |
| `DJANGO_SECURE_SSL_REDIRECT` | Não | Fora do desenvolvimento, todo acesso por HTTP é mandado para HTTPS. `false` só para testar o modo de produção na própria máquina |

## Segurança na hospedagem

Com `DJANGO_DEBUG=false`, o Django passa a exigir HTTPS: manda o HTTP para o HTTPS, liga o HSTS (o navegador só volta por HTTPS durante um ano, inclusive nos subdomínios) e só envia os cookies do `/admin/` por conexão segura. Em qualquer modo, toda resposta diz ao navegador para não abrir a página dentro de outro site, não tratar JSON como página e não vazar o endereço visitado. A API responde com uma política de conteúdo (CSP) que não deixa carregar nada; o `/admin/` tem uma própria, que só aceita arquivos do próprio servidor. Pedido com mais de 1 MB é recusado.

Para conferir: `python manage.py check --deploy` com as variáveis de produção não deve mostrar avisos.

**Proxy e Cloudflare.** O limite de tentativas (login, cadastro, `/admin/`) conta por IP, e o IP só pode vir de quem é de confiança:

- Sem nada na frente: deixe `DJANGO_NUM_PROXIES=0` e `DJANGO_ATRAS_DA_CLOUDFLARE` desligada. Vale o IP da conexão; cabeçalhos como `X-Forwarded-For` são ignorados, porque qualquer um escreve.
- Com a Cloudflare ligada direto ao servidor: `DJANGO_ATRAS_DA_CLOUDFLARE=true`. O cabeçalho `CF-Connecting-IP` só é aceito quando a conexão vem de um IP da Cloudflare (a lista fica em `config/middleware.py`). Quem pular a Cloudflare e chegar direto ao servidor é contado pelo próprio IP.
- Com a Cloudflare e mais o proxy da hospedagem (Render, Railway e parecidos): `DJANGO_ATRAS_DA_CLOUDFLARE=true` e `DJANGO_NUM_PROXIES=1`.

Ligar qualquer um dos dois também faz o Django acreditar no cabeçalho `X-Forwarded-Proto` que o proxy manda para dizer se o visitante usou HTTPS. Se o site entrar em loop de redirecionamento, falta essa configuração. Para o servidor de origem não ser acessado sem passar pela Cloudflare, o ideal é a hospedagem só aceitar conexões dela (Cloudflare Tunnel ou firewall com a lista de IPs da Cloudflare).

Cada endereço IPv6 de um mesmo bloco `/64` conta como um só, porque cada pessoa costuma receber um bloco inteiro e poderia trocar de endereço a cada tentativa.

Sem `DATABASE_URL`, o modo de desenvolvimento usa um SQLite local, apenas para começar rápido. O banco oficial do projeto é o PostgreSQL no Supabase. As tabelas são criadas com `python manage.py migrate`, sem SQL à parte: mudanças no banco entram por novas migrações.
