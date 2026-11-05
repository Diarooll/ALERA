# Graph Report - ALERA  (2026-11-04)

## Corpus Check
- Corpus is ~16,589 words - fits in a single context window. You may not need a graph.

## Summary
- 292 nodes · 351 edges · 30 communities (10 shown, 20 thin omitted)
- Extraction: 84% EXTRACTED · 15% INFERRED · 1% AMBIGUOUS · INFERRED: 52 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Telas e fluxo do morador
- Modelos e migrações
- Cadastro e login (API)
- Login no front-end
- Testes de contas
- Plano e painel da Defesa Civil
- Painel admin.js
- Configuração do Django
- Apps do back-end e dependências
- Rotas e saúde da API
- Configuração dos apps
- Testes gerais
- Produto ALERA e fases
- Foto de alagamento
- Foto de deslizamento
- Ícone envelope
- Ícone cadeado

## God Nodes (most connected - your core abstractions)
1. `Usuario` - 12 edges
2. `LoginTestes` - 12 edges
3. `Back-end ALERA (API Django e DRF)` - 11 edges
4. `CadastroSerializer` - 10 edges
5. `App do morador (app.html)` - 9 edges
6. `CadastroTestes` - 8 edges
7. `ALERA (Acompanhamento Local de Emergencias e Riscos Ambientais)` - 8 edges
8. `Rotas previstas da API` - 8 edges
9. `registrarAlerta()` - 7 edges
10. `Painel de administracao (admin.html)` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Niveis na demo (limites de 30 mm e 50 mm em 24 h)` --semantically_similar_to--> `Niveis de risco (Normal, Atencao, Alerta, Perigo)`  [INFERRED] [semantically similar]
  projeto-fluxo/TELAS.md → README.md
- `Tela de envio de alertas (form-alerta)` --semantically_similar_to--> `Painel da Defesa Civil (secoes e mudanca de nivel)`  [INFERRED] [semantically similar]
  front-end/app/admin.html → projeto-fluxo/TELAS.md
- `Alerta por rua no WhatsApp` --conceptually_related_to--> `WhatsApp Cloud API (fora da demo)`  [AMBIGUOUS]
  README.md → projeto-fluxo/PROJETO.md
- `Geracao do alerta por regras conferiveis` --conceptually_related_to--> `alertas/ (previsoes, regras de risco e historico)`  [INFERRED]
  projeto-fluxo/PROJETO.md → backend/README.md
- `Rotas previstas da API` --conceptually_related_to--> `Status: so estrutura, sem modelos nem rotas de negocio`  [AMBIGUOUS]
  projeto-fluxo/TELAS.md → backend/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Fluxo de mudanca de nivel: origem automatica ou manual, registro em historico e exibicao no app** — projeto_fluxo_projeto_tarefa_agendada, projeto_fluxo_projeto_painel_django_admin, projeto_fluxo_projeto_geracao_do_alerta, projeto_fluxo_projeto_historico_de_niveis, projeto_fluxo_telas_tela_alerta [EXTRACTED 1.00]
- **Autenticacao com JWT e encaminhamento por papel de conta** — backend_requirements_simplejwt, front_end_app_login_pagina, front_end_app_admin_bloqueio_por_papel, readme_contas_por_papel [INFERRED 0.85]
- **Leituras dos gadgets da Fase 2 alimentando o alerta** — readme_sensor_alera, readme_bueiro_alera, projeto_fluxo_projeto_esp32_endpoint, backend_readme_sensores [EXTRACTED 1.00]

## Communities (30 total, 20 thin omitted)

### Community 0 - "Telas e fluxo do morador"
Cohesion: 0.08
Nodes (32): Status: so estrutura, sem modelos nem rotas de negocio, Bloqueio do painel por sessionStorage papel=admin, Secao Alerta do app, Secao Meus dados do app (cadastro), Secao Missoes do app, App do morador (app.html), Secao Ranking do app, Secao Rota do app (+24 more)

### Community 1 - "Modelos e migrações"
Cohesion: 0.08
Nodes (5): UsuarioAdmin, Migration, Migration, Usuario, UsuarioManager

### Community 2 - "Cadastro e login (API)"
Cohesion: 0.10
Nodes (7): CadastroSerializer, LoginSerializer, MeuPerfilSerializer, Meta, CadastroView, LoginView, MeuPerfilView

### Community 3 - "Login no front-end"
Cohesion: 0.09
Nodes (14): cadastroConsentimento, cadastroEmail, cadastroEndereco, cadastroForm, cadastroSenha, CAMPOS_CADASTRO, campoTelefone, configurarFormulario() (+6 more)

### Community 4 - "Testes de contas"
Cohesion: 0.13
Nodes (3): Base, CadastroTestes, LoginTestes

### Community 5 - "Plano e painel da Defesa Civil"
Cohesion: 0.11
Nodes (20): Django 6.1.3, psycopg[binary] 3.3.8, Tela de abrigos do painel, Tela de bueiros do painel, Tela de envio de alertas (form-alerta), Painel de administracao (admin.html), Arquitetura: navegador, API Django, PostgreSQL, tarefa agendada, Historico de niveis com origem e responsavel (+12 more)

### Community 6 - "Painel admin.js"
Cohesion: 0.16
Nodes (20): abrigos, adicionarAoHistorico(), atualizarPrevia(), campoMensagem, campoRua, conferirAdministrador(), confirmacao, contarRuasEmRisco() (+12 more)

### Community 8 - "Apps do back-end e dependências"
Cohesion: 0.12
Nodes (15): alertas/ (previsoes, regras de risco e historico), Back-end ALERA (API Django e DRF), config/ (configuracoes e rotas principais), locais/ (ruas, areas de risco e abrigos), missoes/ (missoes, pontos e ranking), GET /api/saude/, sensores/ (leituras do ESP32, Fase 2), usuarios/ (moradores e login) (+7 more)

### Community 10 - "Configuração dos apps"
Cohesion: 0.12
Nodes (5): AlertasConfig, LocaisConfig, MissoesConfig, SensoresConfig, UsuariosConfig

### Community 12 - "Produto ALERA e fases"
Cohesion: 0.22
Nodes (10): Endpoint de leituras do ESP32, 142 areas de risco geologico, Alerta por rua no WhatsApp, Bueiro ALERA, Defesa Civil, Fase 1: ALERA Web, Fase 2: Gadgets ALERA, Niveis de risco (Normal, Atencao, Alerta, Perigo) (+2 more)

## Ambiguous Edges - Review These
- `Alerta por rua no WhatsApp` → `WhatsApp Cloud API (fora da demo)`  [AMBIGUOUS]
  projeto-fluxo/PROJETO.md · relation: conceptually_related_to
- `Status: prototipo com contas, cadastro e login em banco` → `Status: so estrutura, sem modelos nem rotas de negocio`  [AMBIGUOUS]
  backend/README.md · relation: conceptually_related_to
- `Status: so estrutura, sem modelos nem rotas de negocio` → `Rotas previstas da API`  [AMBIGUOUS]
  projeto-fluxo/TELAS.md · relation: conceptually_related_to
- `App do morador (app.html)` → `Mapa de navegacao`  [AMBIGUOUS]
  projeto-fluxo/TELAS.md · relation: conceptually_related_to
- `Previa do app no site (secao fase-1)` → `Mapa de navegacao`  [AMBIGUOUS]
  projeto-fluxo/TELAS.md · relation: conceptually_related_to

## Knowledge Gaps
- **28 isolated node(s):** `142 areas de risco geologico`, `Secretaria de Obras`, `Status: prototipo com contas, cadastro e login em banco`, `Equipe MonkeyNerds (FIAP, Challenge 2026)`, `config/ (configuracoes e rotas principais)` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 158 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Usuario` connect `Modelos e migrações` to `Cadastro e login (API)`, `Testes de contas`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Usuario` (e.g. with `CadastroSerializer` and `MeuPerfilSerializer`) actually correct?**
  _`Usuario` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `142 areas de risco geologico`, `Secretaria de Obras`, `Status: prototipo com contas, cadastro e login em banco` to the rest of the system?**
  _28 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Telas e fluxo do morador` be split into smaller, more focused modules?**
  _Cohesion score 0.08377896613190731 - nodes in this community are weakly interconnected._
- **Why does `Back-end ALERA (API Django e DRF)` connect `Apps do back-end e dependências` to `Telas e fluxo do morador`, `Plano e painel da Defesa Civil`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Alerta por rua no WhatsApp` and `WhatsApp Cloud API (fora da demo)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Status: prototipo com contas, cadastro e login em banco` and `Status: so estrutura, sem modelos nem rotas de negocio`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._