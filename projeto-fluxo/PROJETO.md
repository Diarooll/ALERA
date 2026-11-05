# ALERA: stack e funcionamento

Este documento registra como o ALERA será construído. Para conhecer o projeto e abrir o protótipo, veja o [README](../README.md). Para ver cada tela e fluxo, veja [TELAS.md](TELAS.md).

> **Status:** planejamento. O back-end descrito aqui ainda não existe.

## Objetivo desta etapa

Fazer uma **demo de ponta a ponta para a FIAP**, com dados e telefones de teste: uma previsão de chuva gera um nível de risco para uma rua, e o alerta chega de verdade no WhatsApp.

O uso com moradores reais não faz parte desta etapa.

## Stack

### Decisões da equipe

| Camada | Escolha |
| --- | --- |
| Back-end | Python + Django |
| Painel administrativo | Django Admin |
| Comunicação | Front-end separado, falando com o back-end por API |
| Banco de dados | PostgreSQL |
| Front-end agora | HTML, CSS e JavaScript puro, com `fetch` |
| Hospedagem | Serviços gerenciados |
| WhatsApp | API oficial da Meta (WhatsApp Cloud API) |

Ficam para depois:

- **React:** substitui o front-end puro em uma migração futura.
- **PostGIS e GeoDjango:** entram quando houver polígonos das áreas de risco ou cálculo de distância real.

### Sugestões a confirmar

Estes itens ainda não foram decididos pela equipe.

| Item | Sugestão | Motivo |
| --- | --- | --- |
| API | Django REST Framework + `django-cors-headers` | É o padrão com Django, e o front-end fica em outro domínio |
| Login | Contas do Django + `djangorestframework-simplejwt` | Evita a complicação de cookies entre domínios |
| Hospedagem do front-end | Netlify | Serve bem um site estático |
| Hospedagem da API | Render | Serviço gerenciado para Python |
| Banco gerenciado | Supabase, usado só como PostgreSQL | Oferece PostGIS para o futuro; o login continua no Django |
| Tarefa de alertas | Comando do Django executado por cron | É simples e suficiente para a demo |
| Previsão do tempo | Open-Meteo | Facilita os testes; termos e precisão ainda precisam ser conferidos |

Confira limites e preços dos serviços antes de contratar.

## Arquitetura

```text
Navegador (HTML, CSS e JS)
        │  fetch
        ▼
API Django ───── PostgreSQL
                     ▲
Tarefa agendada ─────┘
   ├── busca a previsão na API de clima
   ├── define o nível de risco de cada área
   └── envia o alerta pela API do WhatsApp
```

## Como as coisas vão funcionar

### Cadastro e login

1. O morador cria a conta no front-end, com telefone, senha e rua.
2. O front-end envia os dados para a API, que valida e salva no banco.
3. O login devolve um token, usado nas próximas chamadas à API.

### Ruas e áreas de risco

A equipe cadastra ruas, áreas de risco e abrigos no Django Admin. Na demo, uma tabela simples liga cada rua a uma área de risco, preenchida à mão para algumas ruas de exemplo.

### Geração do alerta

1. A tarefa agendada busca a previsão de chuva.
2. Regras fixas no código definem o nível: Normal, Atenção, Alerta ou Perigo.
3. O sistema encontra os moradores das ruas afetadas.
4. O alerta é enviado no WhatsApp com a rua, o nível, o que fazer e o abrigo.
5. O banco registra o que foi enviado, para quem, quando e o resultado do envio.

O nível sempre vem de regras que podem ser conferidas. Se a IA for usada, será apenas para redigir o texto da mensagem.

### Telas do app

As telas de Alerta, Missões, Ranking e Meus dados deixam de ter valores fixos no HTML e passam a buscar os dados na API com `fetch`.

### Missões e ranking

O morador conclui uma missão, a API registra os pontos e o ranking soma os pontos por rua.

### Fase 2: gadgets

O ESP32 envia as leituras do Sensor ALERA e do Bueiro ALERA para um endpoint da API. Elas ficam em uma tabela do mesmo PostgreSQL e passam a influenciar o alerta.

## Organização prevista do back-end

```text
backend/
├── config/    # configurações do projeto Django
├── usuarios/  # moradores e login
├── locais/    # ruas, áreas de risco e abrigos
├── alertas/   # previsões, regras de risco e envio no WhatsApp
├── missoes/   # missões, pontos e ranking
└── sensores/  # leituras do ESP32 (Fase 2)
```

## Fora desta etapa

- React e PostGIS
- App nativo
- SMS e Telegram
- Filas com Celery e Redis
- Uso com moradores reais

## Pendências

- **Áreas de risco:** descobrir de onde virão os dados das 142 áreas e em que formato.
- **Limites de risco:** os valores atuais são de demonstração e precisam de validação técnica antes de qualquer uso real.
- **WhatsApp:** configurar a conta da Meta e os números de teste. O uso real exige modelos de mensagem aprovados.
- **Antes de atender moradores reais:** tratar LGPD e consentimento, criar um plano para falhas no envio e monitorar o sistema.
