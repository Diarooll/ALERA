# ALERA: back-end

API em Django e Django REST Framework. Por enquanto só existe a estrutura: não há modelos de negócio nem rotas além da verificação de saúde.

## Pastas

| Pasta | Função |
| --- | --- |
| `config/` | Configurações e rotas principais |
| `usuarios/` | Moradores e login |
| `locais/` | Ruas, áreas de risco e abrigos |
| `alertas/` | Previsões, regras de risco e envio no WhatsApp |
| `missoes/` | Missões, pontos e ranking |
| `sensores/` | Leituras do ESP32 (Fase 2) |

## Como rodar no Windows (PowerShell)

Dentro da pasta `backend`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crie o arquivo `backend/.env` com `DJANGO_DEBUG=true`. Depois:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Saúde da API: <http://127.0.0.1:8000/api/saude/>
- Django Admin: <http://127.0.0.1:8000/admin/>

Para rodar os testes:

```powershell
python manage.py test
```

## Variáveis de ambiente

| Variável | Obrigatória | Uso |
| --- | --- | --- |
| `DJANGO_DEBUG` | Não | `true` só em desenvolvimento |
| `DJANGO_SECRET_KEY` | Fora do modo de desenvolvimento | Chave secreta do Django |
| `DATABASE_URL` | Fora do modo de desenvolvimento | Conexão com o PostgreSQL, como `postgres://usuario:senha@host:5432/alera` |
| `DJANGO_ALLOWED_HOSTS` | Fora do modo de desenvolvimento | Domínios da API, separados por vírgula |
| `CORS_ALLOWED_ORIGINS` | Quando o front-end chamar a API | Endereços do front-end, separados por vírgula, como `http://127.0.0.1:5500` |

Sem `DATABASE_URL`, o modo de desenvolvimento usa um SQLite local, apenas para começar rápido. O banco oficial do projeto é o PostgreSQL.
