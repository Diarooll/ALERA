# ALERA: stack e funcionamento

Este documento registra como o ALERA será construído. Para conhecer o projeto e abrir o protótipo, veja o [README](../README.md). Para ver cada tela e fluxo, veja [TELAS.md](TELAS.md).

> **Status:** em construção. A estrutura do back-end já existe em `backend/`, mas as regras e as rotas descritas aqui ainda não foram feitas.

## Objetivo desta etapa

Fazer uma **demo de ponta a ponta para a FIAP**, com dados de teste: uma previsão de chuva ou a Defesa Civil define o nível de risco de uma área, e o alerta aparece no app para os moradores daquela rua.

O uso com moradores reais não faz parte desta etapa.

## Stack

### Decisões da equipe

| Camada | Escolha |
| --- | --- |
| Back-end | Python + Django |
| Painel da Defesa Civil | Página feita no Django Admin |
| Comunicação | Front-end separado, falando com o back-end por API |
| Banco de dados | PostgreSQL, com as tabelas criadas pelo Victor, separadamente |
| Front-end agora | HTML, CSS e JavaScript puro, com `fetch` |
| Hospedagem | Serviços gerenciados |

Ficam para depois:

- **WhatsApp:** não entra na demo. Quando entrar, usará a API oficial da Meta (WhatsApp Cloud API).
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
                     ▲ ▲
Tarefa agendada ─────┘ │
   ├── busca a previsão na API de clima
   └── define o nível de risco de cada área
                       │
Defesa Civil ──────────┘
   └── muda o nível de uma área pelo painel no Django Admin
```

## Como as coisas vão funcionar

### Cadastro e login

1. O morador cria a conta no front-end, com e-mail, senha, telefone e rua.
2. O front-end envia os dados para a API, que valida e salva no banco.
3. O morador entra com e-mail e senha, e o login devolve um token, usado nas próximas chamadas à API.

A Defesa Civil tem acesso próprio ao painel no Django Admin.

### Ruas e áreas de risco

Ruas, áreas de risco e abrigos são cadastrados no Django Admin. Na demo, cada rua pertence a uma área de risco, preenchida à mão para algumas ruas de exemplo.

### Geração do alerta

1. A tarefa agendada busca a previsão de chuva, e regras fixas no código definem o nível: Normal, Atenção ou Alerta.
2. A Defesa Civil também pode mudar o nível de uma área pelo painel, inclusive para Perigo.
3. O banco atualiza o nível da área e registra a mudança no histórico, com a origem e o responsável.
4. O morador vê na tela de Alerta o nível, o que fazer e o abrigo da própria rua.

O nível automático sempre vem de regras que podem ser conferidas. Se a IA for usada, será apenas para redigir o texto do alerta.

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
├── alertas/   # previsões, regras de risco e histórico de níveis
├── missoes/   # missões, pontos e ranking
└── sensores/  # leituras do ESP32 (Fase 2)
```

## Fora desta etapa

- WhatsApp, SMS e Telegram
- React e PostGIS
- App nativo
- Filas com Celery e Redis
- Uso com moradores reais

## Pendências

- **Áreas de risco:** descobrir de onde virão os dados das 142 áreas e em que formato.
- **Limites de risco:** os valores atuais são de demonstração e precisam de validação técnica antes de qualquer uso real.
- **Painel da Defesa Civil:** definir com o Victor o que acontece com o `front-end/app/admin.html` e como o login leva a Defesa Civil até o Django Admin.
- **Quando o WhatsApp entrar:** configurar a conta da Meta, criar uma tabela de envios e aprovar os modelos de mensagem para uso real.
- **Antes de atender moradores reais:** tratar LGPD e consentimento, criar um plano para falhas e monitorar o sistema.
