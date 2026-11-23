# ALERA: telas e fluxos

Este documento descreve como o ALERA vai ficar por fora na demo para a FIAP: o que cada tela mostra, o que cada botão faz e o que acontece quando algo dá errado. A stack está em [PROJETO.md](PROJETO.md).

> **Status:** proposta para a equipe revisar. Nada disto foi implementado. Rotas, campos e textos ainda podem mudar.

## Princípios

- **O visual atual continua:** cores, fontes e componentes seguem `front-end/css/tokens.css` e o protótipo existente.
- **Celular primeiro:** no celular, o menu fica em abas embaixo. No computador, fica no topo.
- **Ligar 199 sempre disponível:** o botão é um link `tel:199`, então funciona mesmo se a API estiver fora do ar.
- **Nunca passar falsa segurança:** se os dados estiverem desatualizados ou indisponíveis, o app diz isso em vez de mostrar "Normal".
- **Demo identificada:** a interface deixa claro que os dados e limites são de demonstração.

## Mapa de navegação

```text
Site (site.html)
  └── Testar o app ──► Login ◄──► Criar conta
                         │
                         ▼
                 App (exige login)
   ┌──────────┬──────────┴───────┬─────────────┐
   ▼          ▼                  ▼             ▼
 Alerta     Missões            Ranking     Meus dados
   │          │
   ▼          ▼
 Rota      Detalhe da missão

Defesa Civil ──► Painel no Django Admin ──► Muda o nível da área ──► Aparece no app
```

## Comportamentos comuns do app

| Situação | O que a pessoa vê |
| --- | --- |
| Sem login | Vai para a tela de Login e, depois de entrar, volta para onde estava |
| Sessão expirada | Vê "Sua sessão expirou. Entre de novo." na tela de Login |
| Carregando | Blocos cinza no lugar do conteúdo; os botões Ligar 199 e Voltar continuam ativos |
| Sem conexão ou API fora do ar | Vê "Não foi possível atualizar. Em caso de risco, ligue 199.", com o botão Tentar de novo |
| Tema claro ou escuro | A escolha fica salva no navegador e vale para o site, o login e o app |

## Site

**Arquivo:** `front-end/site.html`. **Acesso:** público. **API:** nenhuma.

O site continua estático, com as seções atuais: início, O problema, ALERA Web, Gamificação, Gadgets, Quem somos e Referências.

Mudanças propostas:

- Todos os botões que levam ao app passam pelo Login. Quem já estiver logado entra direto.
- Limites de chuva e inclinação ganham a nota "valores de demonstração".
- Missões e pontos ficam iguais aos do app.

## Login

**Arquivo:** `front-end/app/login.html`. **Acesso:** público. **API:** `POST /api/auth/login/`.

```text
┌──────────────────────────────┐
│           A.L.E.R.A          │
│      Bem-vindo de volta!     │
│ Não tem uma conta? Criar conta│
│                              │
│ E-mail                       │
│ [ voce@exemplo.com         ] │
│ Senha                        │
│ [ ••••••••              👁 ] │
│                              │
│ [          Entrar          ] │
└──────────────────────────────┘
```

| Ação ou situação | Resultado |
| --- | --- |
| Dados corretos de morador | Abre o app na tela de Alerta |
| Dados corretos da Defesa Civil | Abre o painel da Defesa Civil, no Django Admin |
| Campo vazio ou inválido | Mostra o erro abaixo do campo e coloca o foco nele |
| E-mail ou senha incorretos | Mostra "E-mail ou senha incorretos.", sem dizer qual dos dois |
| Enviando | O botão fica desativado e mostra "Aguarde..." |

Na demo, o link "Recuperar senha" sai da tela, porque ainda não haverá essa função. Se alguém esquecer a senha, a equipe redefine pelo Admin.

## Criar conta

**Arquivo:** `front-end/app/login.html#cadastro`. **Acesso:** público. **API:** `GET /api/ruas/` e `POST /api/auth/cadastro/`.

```text
┌──────────────────────────────┐
│       Crie sua conta         │
│ Já tem uma conta? Entrar     │
│                              │
│ E-mail                       │
│ [ voce@exemplo.com         ] │
│ Senha                        │
│ [ Mínimo de 8 caracteres   ] │
│ Telefone                     │
│ [ (32) 99999-0000          ] │
│ Sua rua                      │
│ [ Selecione a rua        ▼ ] │
│                              │
│ [ ] Aceito que meus dados    │
│     sejam usados para mostrar│
│     alertas da minha rua.    │
│                              │
│ [        Criar conta       ] │
└──────────────────────────────┘
```

- **Campos:** o cadastro pede e-mail, senha, telefone e rua. O endereço completo sai.
- **Rua em lista:** a pessoa escolhe entre as ruas de demonstração. Assim, o sistema sempre sabe ligar a rua a uma área de risco.
- **Telefone:** aceita apenas celular com DDD, já pensando no envio pelo WhatsApp depois da demo.
- **Sucesso:** a conta é salva de verdade e a pessoa entra direto no app, sem `alert()`.
- **E-mail já cadastrado:** mostra "Este e-mail já tem conta. Entrar?".

## Alerta

**Arquivo:** `front-end/app/app.html#alerta`. É a tela inicial do app. **API:** `GET /api/alerta-atual/`.

```text
┌──────────────────────────────┐
│ A.L.E.R.A           ☎ 199  ☾ │
├──────────────────────────────┤
│ Rua Exemplo                  │
│ Bairro Exemplo · há 5 min    │
├──────────────────────────────┤
│ ▲ ALERTA                     │
│ Previsão de 60 mm nas        │
│ próximas 24 h. Deixe os      │
│ documentos à mão.            │
│ ███ ███ ███ ░░░  Nível 3 de 4│
├──────────────────────────────┤
│ [ mapa ilustrativo ]         │
│ Seu abrigo                   │
│ Escola Municipal Exemplo     │
│ 600 m · 8 min a pé           │
│ [      Ver rota segura     ] │
│ [  ☎ Ligar 199 · Defesa Civil]│
├──────────────────────────────┤
│ O que fazer em cada nível    │
├──────────────────────────────┤
│ Alerta  Missões Ranking Dados│
└──────────────────────────────┘
```

### Níveis na demo

| Nível | Regra de demonstração | Texto para o morador |
| --- | --- | --- |
| Normal | Menos de 30 mm previstos em 24 h | Sem alerta para sua rua agora. Em caso de risco, ligue 199. |
| Atenção | 30 mm ou mais em 24 h | Chuva prevista. Confira seu abrigo e tire o lixo da frente do bueiro. |
| Alerta | 50 mm ou mais em 24 h | Chuva forte prevista. Evite a rua e deixe os documentos à mão. |
| Perigo | Definido pela Defesa Civil no painel | Risco agora. Saia de casa e vá para o abrigo. |

### Estados especiais

| Situação | O que muda |
| --- | --- |
| Previsão desatualizada há mais de 3 horas | Em vez do nível, mostra "Sem dados recentes da sua rua. Fique atento e, em caso de risco, ligue 199." |
| Nenhum abrigo salvo | Mostra o abrigo mais perto cadastrado, com o botão "Salvar este abrigo" |
| Nível Perigo | A faixa fica vermelha, e "Ver rota segura" e "Ligar 199" sobem para logo abaixo da mensagem |

O mapa deve exibir sempre a legenda "Mapa ilustrativo", porque a demo não calcula rotas reais.

## Rota segura

**Arquivo:** `front-end/app/app.html#rota`. **API:** usa o abrigo vindo de `GET /api/alerta-atual/`.

```text
┌──────────────────────────────┐
│ ‹ Voltar                     │
│ Rota até o abrigo            │
├──────────────────────────────┤
│ [ mapa ilustrativo ]         │
│ Escola Municipal Exemplo     │
│ 8 min a pé · 600 m           │
│ ▲ Não passe pela Rua Exemplo │
│ 1. Desça 50 m até a Rua da Paz│
│ 2. Vire à direita e siga 300 m│
│ 3. Suba a Av. Exemplo 250 m  │
│ [   Abrir no Google Maps   ] │
│ [  ☎ Ligar 199 · Defesa Civil]│
└──────────────────────────────┘
```

Na demo, passos e desenho do mapa são cadastrados à mão para cada abrigo. O título muda de "Rota segura" para "Rota até o abrigo" porque o sistema ainda não verifica em tempo real se o caminho está seguro. O aviso de rua a evitar só aparece quando houver alerta para ela.

## Missões

**Arquivo:** `front-end/app/app.html#missoes`. **API:** `GET /api/missoes/` e `POST /api/missoes/{id}/concluir/`.

```text
┌──────────────────────────────┐
│ Suas missões        120 pts  │
│ Ações que protegem sua rua   │
├──────────────────────────────┤
│ Limpe o bueiro       +50 pts │
│ ▓▓▓▓▓▓░░░░ 3 de 5 vizinhos   │
│ [ Ver detalhes             ›]│
├──────────────────────────────┤
│ Reporte lixo         +20 pts │
│ Não iniciada                 │
│ [ Reportar                 ›]│
├──────────────────────────────┤
│ Plante uma muda      +80 pts │
│ Não iniciada                 │
│ [ Ver áreas para plantar   ›]│
├──────────────────────────────┤
│ Salve seu abrigo     +10 pts │
│ ✓ Concluída                  │
│ [ Trocar abrigo            ›]│
└──────────────────────────────┘
```

As mesmas quatro missões e os mesmos pontos aparecem no site e no app. Os valores acima são os do site atual.

### Detalhes das missões

Cada detalhe abre por cima da lista. O foco vai para a janela, e `Esc` ou o botão Fechar voltam para a lista.

| Missão | O que a tela mostra | Como conclui |
| --- | --- | --- |
| Limpe o bueiro | Orientações de segurança e o aviso "Com a água subindo, não chegue perto: ligue 199". O mapa dos bueiros fica como prévia da Fase 2 | "Limpei o bueiro", confirmado pelo próprio morador |
| Reporte lixo | Campo de local e descrição | Envio do relato, que fica visível no painel |
| Plante uma muda | Áreas de exemplo e orientação para plantar só em local autorizado | "Plantei a muda", confirmado pelo próprio morador |
| Salve seu abrigo | Abrigos no mapa e em lista | "Salvar este abrigo", via `PUT /api/me/abrigo/`. O abrigo passa a aparecer no Alerta e na Rota, e continua salvo depois de recarregar |

Cada morador recebe os pontos de cada missão uma única vez. Na demo, as confirmações não são verificadas, e a tela informa isso.

## Ranking

**Arquivo:** `front-end/app/app.html#ranking`. **API:** `GET /api/ranking/`.

```text
┌──────────────────────────────┐
│ Ranking das ruas             │
│ Bairro Exemplo               │
├──────────────────────────────┤
│ 1  Rua das Flores  1.240 pts │
│ 2  Rua Exemplo       980 pts │
│    sua rua                   │
│ 3  Rua da Paz        760 pts │
├──────────────────────────────┤
│ Dados de demonstração        │
└──────────────────────────────┘
```

O ranking soma os pontos dos moradores por rua e destaca a rua de quem está logado. Sem pontos no bairro, mostra "Ainda sem pontos no bairro. Conclua uma missão e comece o ranking.".

## Meus dados

**Arquivo:** `front-end/app/app.html#cadastro`. **API:** `GET /api/me/`, `PATCH /api/me/` e `DELETE /api/me/`.

```text
┌──────────────────────────────┐
│ Meus dados                   │
├──────────────────────────────┤
│ E-mail                       │
│ [ voce@exemplo.com         ] │
│ Telefone                     │
│ [ (32) 99999-0000          ] │
│ Sua rua                      │
│ [ Rua Exemplo            ▼ ] │
│                              │
│ [     Salvar alterações    ] │
│ [           Sair           ] │
│ Excluir minha conta          │
└──────────────────────────────┘
```

- **Salvar:** mostra "Dados salvos." na própria tela. A tela de Alerta passa a usar a nova rua.
- **Sair:** apaga a sessão do navegador e volta para o Login.
- **Excluir conta:** pede confirmação e remove os dados pessoais do morador.

## Mensagem no WhatsApp (depois da demo)

O WhatsApp não entra na demo. Este é o modelo previsto para quando o envio for implementado:

```text
ALERA · Rua Exemplo, Bairro Exemplo
Nível ALERTA (3 de 4)

Previsão de 60 mm nas próximas 24 h.
O que fazer: evite a rua e deixe os documentos à mão.

Abrigo: Escola Municipal Exemplo, 600 m
Ver no app: <link>
Emergência: ligue 199

```

A ideia é o morador só receber mensagem quando o nível da rua subir ou chegar a Perigo, para não repetir o mesmo aviso. Esse texto precisará virar um modelo aprovado na Meta para uso real.

## Painel da Defesa Civil (Django Admin)

**Acesso:** só a Defesa Civil e a equipe. É o dashboard do projeto, feito com as telas do Django Admin e estas seções:

| Seção | Para que serve |
| --- | --- |
| Ruas e áreas de risco | Cadastrar as ruas de demonstração e ligar cada uma a uma área |
| Abrigos | Cadastrar nome, distância, situação, passos da rota e desenho do mapa |
| Moradores | Consultar contas e redefinir senhas |
| Previsões | Ver a última previsão recebida e o nível calculado |
| Histórico de níveis | Ver cada mudança de nível, com horário, origem e responsável |
| Missões e relatos | Editar missões e ler os relatos de lixo |

### Mudar o nível de uma área

A Defesa Civil escolhe uma área e um nível, confirma a mudança, e o novo nível aparece no app dos moradores daquela área. A mudança fica registrada no histórico. Isso também garante a apresentação, porque pode não chover no dia.

O painel deve exibir a etiqueta "Demonstração", para não parecer que a Defesa Civil já usa o sistema ou que o alerta é oficial.

## Roteiro da demo

1. Abrir o site e mostrar o problema.
2. Clicar em "Testar o app" e criar uma conta com um e-mail e um celular de teste.
3. Ver a tela de Alerta no nível Normal e salvar um abrigo.
4. No painel da Defesa Civil, mudar o nível da área dessa rua.
5. Atualizar o app, ver o novo nível e abrir a rota até o abrigo.
6. Concluir uma missão e ver os pontos no ranking.

## Rotas previstas da API

| Método e rota | Função | Exige login |
| --- | --- | --- |
| `POST /api/auth/cadastro/` | Criar conta | Não |
| `POST /api/auth/login/` | Entrar | Não |
| `GET /api/ruas/` | Listar ruas disponíveis | Não |
| `GET /api/me/` | Ver os próprios dados | Sim |
| `PATCH /api/me/` | Alterar dados | Sim |
| `DELETE /api/me/` | Excluir a conta | Sim |
| `PUT /api/me/abrigo/` | Salvar o abrigo | Sim |
| `GET /api/alerta-atual/` | Ver nível, mensagem e abrigo da rua | Sim |
| `GET /api/abrigos/` | Listar abrigos próximos | Sim |
| `GET /api/missoes/` | Listar missões e progresso | Sim |
| `POST /api/missoes/{id}/concluir/` | Concluir uma missão | Sim |
| `GET /api/ranking/` | Ver o ranking do bairro | Sim |
