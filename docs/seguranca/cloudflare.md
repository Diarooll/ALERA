# ALERA atrás da Cloudflare: passo a passo de segurança

Este guia mostra como configurar a Cloudflare na frente do ALERA. Ele não cria conta nem usa chave nenhuma: são os passos para a equipe fazer no painel. Quase tudo funciona no **plano Free**. Quando algo pede plano pago, o guia avisa.

Os nomes dos menus do painel podem mudar um pouco com o tempo. Se não achar um item, procure pelo nome em inglês, que aparece entre parênteses.

## Antes de começar: palavras que aparecem aqui

- **Borda**: os servidores da Cloudflare. O visitante fala com eles primeiro, e eles repassam o pedido para o ALERA.
- **Origem**: o nosso servidor de verdade. No ALERA são dois: o site (Cloudflare Pages) e a API Django.
- **Nuvem laranja (Proxied)**: no DNS da Cloudflare, um registro com a nuvem laranja passa pela borda. Com a nuvem cinza, o visitante vai direto na origem e nenhuma proteção deste guia vale.
- **WAF**: o "porteiro" da Cloudflare. Olha cada pedido e bloqueia o que bate com uma regra.
- **Rate limiting**: limite de pedidos por IP num intervalo de tempo.
- **Cabeçalho (header)**: um recado que vai junto com o pedido ou com a resposta.

## Como as peças ficam

```
Morador ou equipe (navegador)
        |
        v
+--------------------- Cloudflare (a borda) ---------------------+
|  HTTPS  ->  WAF (regras)  ->  limite de tentativas  ->  cache  |
+----------------------------------------------------------------+
        |                                   |
        v                                   v
SEU-DOMINIO.com.br                   api.SEU-DOMINIO.com.br
Cloudflare Pages                     Cloudflare Tunnel
(pasta front-end/ e os               -> Django em 127.0.0.1:8000
 cabeçalhos do front-end/_headers)      (servidor sem porta aberta)
```

Em todo este guia, **troque `SEU-DOMINIO.com.br` pelo domínio real**. Os lugares são:

1. `front-end/_headers`, na linha `connect-src` (e no modelo do Turnstile, se usar).
2. `front-end/js/api.js`, na constante `API_URL` (fica `https://api.SEU-DOMINIO.com.br/api`).
3. As expressões das regras de WAF, de limite e de cache deste guia.
4. As variáveis do Django: `DJANGO_ALLOWED_HOSTS` e `CORS_ALLOWED_ORIGINS` (veja a seção 9).

---

## 1. Publicar o front-end no Cloudflare Pages

1. Em **Workers e Pages** (Workers & Pages), crie um projeto do Pages ligado ao repositório.
2. Ramo de produção: `main`. Comando de build: **vazio**. Pasta de saída (Build output directory): **`front-end`**.
   - Só a pasta `front-end/` vai para o ar. O `backend/` e o resto do repositório não ficam públicos.
   - O arquivo `front-end/_headers` precisa estar na raiz dessa pasta. Com outra pasta de saída, o Pages não acha o arquivo e o site fica sem as proteções.
3. Em **Domínios personalizados** (Custom domains), ligue `SEU-DOMINIO.com.br` ao projeto.
4. Proteja as prévias. Cada ramo e cada PR ganha um endereço `algo.NOME-DO-PROJETO.pages.dev`. Nas configurações do projeto, ative a política de acesso das prévias (Access policy). Assim só a equipe abre as versões em teste.

### O que o `_headers` faz

O arquivo já está pronto e comentado linha por linha. Em resumo:

| Cabeçalho | Protege contra |
| --- | --- |
| `Content-Security-Policy` (CSP) | Script injetado na página (XSS). A página só carrega coisas de uma lista de endereços. |
| `Strict-Transport-Security` (HSTS) | Alguém forçar a conexão sem `https` num Wi-Fi público. |
| `X-Content-Type-Options: nosniff` | O navegador tratar um arquivo de texto como script. |
| `Referrer-Policy` | Vazar o caminho completo das páginas para outros sites. |
| `Permissions-Policy` | Uso de câmera, microfone, GPS etc. que o ALERA não usa. |
| `X-Frame-Options` e `frame-ancestors` | Outro site abrir o ALERA escondido num iframe para enganar cliques (clickjacking). |
| `Cross-Origin-Opener-Policy` | Uma aba de outro site mexer na aba do ALERA. |
| `Cache-Control` | HTML sempre novo; imagens, CSS e JS guardados no navegador. |
| `X-Robots-Tag` | O Google listar as páginas do app e o endereço `pages.dev`. |

### Domínios de fora que a CSP libera

Qualquer endereço de fora que não estiver nesta lista é bloqueado pelo navegador.

| Domínio | Para quê | Diretiva |
| --- | --- | --- |
| `https://fonts.googleapis.com` | CSS das fontes (Google Fonts) | `style-src` |
| `https://fonts.gstatic.com` | Arquivos das fontes | `font-src` |
| `https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/` | Leaflet: JS, CSS e imagens. Só esta pasta. | `script-src`, `style-src`, `img-src` |
| `https://tile.openstreetmap.org` | Os quadradinhos do mapa | `img-src` |
| `https://viacep.com.br` | Busca do CEP | `connect-src` |
| `https://api.SEU-DOMINIO.com.br` | A nossa API (trocar pelo endereço real) | `connect-src` |

Links comuns (`<a href>`) para notícias ou para o Google Maps **não** precisam estar na lista. A CSP controla o que a página carrega, não para onde a pessoa navega.

### Duas coisas que o front-end precisa saber

1. **Nada de JavaScript dentro do HTML.** `<script>` com código escrito no próprio HTML, `onclick="..."` e `href="javascript:..."` não rodam. Hoje `app/app.html` e `app/admin.html` têm um `<script>` curto no `<head>`: a "guarda" que manda para o login quem não entrou. Ele precisa ir para um arquivo (por exemplo `js/guarda-app.js` e `js/guarda-admin.js`), carregado com `<script src="...">` no mesmo lugar do `<head>`. Sem isso, a guarda não roda. O app continua seguro, porque quem confere de verdade é o servidor, mas a tela do app pisca antes de ir para o login.
2. **Domínio novo só combinando antes.** Biblioteca, fonte ou serviço de outro endereço precisa entrar na CSP. Senão, quebra no site publicado (no computador funciona, porque lá não tem CSP).

### Como testar

1. Publique num ramo de teste e abra a prévia.
2. Aperte F12, aba **Console**. Navegue pelo site, pelo login, pelo app e pelo painel, com o mapa aberto.
3. Não pode aparecer erro com "Content Security Policy" ou "Refused to load". Se aparecer, o erro diz qual endereço foi barrado e qual diretiva barrou.
4. Na aba **Rede** (Network), clique na página e confira em "Response Headers" se os cabeçalhos estão lá.
5. Ferramenta externa opcional: o [Mozilla Observatory](https://developer.mozilla.org/en-US/observatory) dá uma nota para os cabeçalhos.

### Por que não tem `_redirects`

Não faz falta. O `http` para `https` é feito pela Cloudflare ("Always Use HTTPS", seção 2). O Pages já tira o `.html` dos endereços sozinho (`/app/login.html` vira `/app/login`). E o Pages não consegue repassar pedidos para a API em outro servidor. Por isso a API fica em `api.SEU-DOMINIO.com.br`.

---

## 2. SSL/TLS: tudo com cadeado

No painel do domínio, menu **SSL/TLS**:

1. **Modo de criptografia: Full (strict)**, em SSL/TLS > Visão geral (Overview).
   - *Flexible*: a Cloudflare fala com a origem **sem** criptografia. Nunca use.
   - *Full*: com criptografia, mas aceita qualquer certificado, até falso.
   - *Full (strict)*: com criptografia e certificado válido. É o certo.
   - Se a API usar o Tunnel (seção 3), o túnel já vai criptografado. Deixe Full (strict) mesmo assim, para o domínio todo.
   - Se a API rodar num servidor com IP público (VPS), instale nele um **Origin Certificate** da Cloudflare (SSL/TLS > Servidor de origem, ou Origin Server). É grátis e vale para o Full (strict).
2. Em SSL/TLS > **Certificados de borda** (Edge Certificates):
   - **Always Use HTTPS**: ligado. Todo `http://` vira `https://`.
   - **Versão mínima do TLS** (Minimum TLS Version): **TLS 1.2**. As versões 1.0 e 1.1 são velhas e quebráveis.
   - **TLS 1.3**: ligado.
   - **Automatic HTTPS Rewrites**: ligado.
   - **HSTS**: ligue **só depois** de conferir que o site e a API abrem com `https`. Use:
     - Max-Age: **6 meses**, o mesmo valor do `_headers` (`max-age=15552000`);
     - Include subdomains: ligado, se todos os subdomínios tiverem `https`;
     - Preload: **desligado**;
     - No-Sniff: ligado.

   **Cuidado com o HSTS:** ele "gruda" no navegador. Se o `https` quebrar, quem já visitou fica sem acesso até o prazo vencer. Por isso, primeiro confirme que o `https` funciona, e só depois ligue.

   O `_headers` também manda o HSTS. Com os dois ligados, o cabeçalho pode aparecer duas vezes. Não tem problema: o navegador usa o primeiro. Só mantenha os mesmos valores nos dois.

---

## 3. Proteger a origem do Django

### Por que isso importa

A Cloudflare só protege quem passa por ela. Se a API também responder direto pelo IP ou por outro endereço do servidor, um atacante pula a borda e escapa do WAF e do limite de tentativas.

Tem um segundo motivo. Quando a Cloudflare repassa um pedido, ela escreve no cabeçalho **`CF-Connecting-IP`** o IP de verdade de quem acessou. Ela sempre sobrescreve esse cabeçalho, então quem passa pela borda não consegue mentir nele. Mas quem fala **direto** com o Django escreve o que quiser ali.

O Django vai passar a usar esse cabeçalho para contar as tentativas de login por IP. Outro agente está fazendo isso, ligado por uma variável de ambiente. Se a origem estiver aberta, um atacante manda um IP inventado em cada tentativa, e o limite de "10 logins por minuto" deixa de existir.

**Regra:** só ligue a variável que faz o Django confiar no `CF-Connecting-IP` depois de fazer a opção A, a B ou a C abaixo e passar no teste do fim desta seção.

### Opção A (recomendada): Cloudflare Tunnel

O servidor abre uma conexão **de dentro para fora** até a Cloudflare. Ele não precisa de nenhuma porta aberta na internet, então não tem como alguém chegar no Django sem passar pela borda.

1. No painel **Zero Trust**, vá em Redes > Túneis (Networks > Tunnels) > Criar túnel. Escolha **Cloudflared** e dê o nome `alera-api`.
2. O painel mostra um comando para instalar o `cloudflared` no servidor, com um **token**. Esse token é uma senha: não vai para o Git, não vai em conversa, não vai em print.
3. Em **Public hostname**, preencha o subdomínio `api`, o domínio `SEU-DOMINIO.com.br`, o tipo `HTTP` e o endereço `127.0.0.1:8000`. O painel cria sozinho o DNS do `api`, com a nuvem laranja.
4. No servidor, o Django (gunicorn) escuta **só** em `127.0.0.1:8000`, por exemplo com `gunicorn config.wsgi --bind 127.0.0.1:8000`.
5. No firewall do servidor, feche toda entrada, menos o SSH (de preferência só com chave).

**Atenção:** com o Tunnel, todo pedido chega ao Django vindo de `127.0.0.1`. Se o Django não ler o `CF-Connecting-IP`, ele acha que todo mundo é a mesma pessoa. Aí um atacante errando a senha bloqueia o login de **todos** os moradores. Com o Tunnel, a variável do `CF-Connecting-IP` **precisa** ficar ligada.

### Opção B: servidor com IP público (VPS)

1. **Firewall aceitando só a Cloudflare.** A lista oficial de IPs está em `https://www.cloudflare.com/ips-v4` e `https://www.cloudflare.com/ips-v6`. Exemplo com `ufw` no Linux:

   ```bash
   sudo ufw default deny incoming
   sudo ufw allow OpenSSH            # primeiro o SSH, para não se trancar fora
   for ip in $(curl -s https://www.cloudflare.com/ips-v4) $(curl -s https://www.cloudflare.com/ips-v6); do
     sudo ufw allow proto tcp from "$ip" to any port 443
   done
   sudo ufw enable
   ```

   A lista muda pouco, mas muda. Confira de tempos em tempos.
2. **Authenticated Origin Pulls**, em SSL/TLS > Servidor de origem. A Cloudflare apresenta um certificado ao se conectar, e o servidor (nginx) recusa quem não apresentar. Funciona no plano Free.
   - O certificado padrão da Cloudflare é **o mesmo para todas as contas**. Ele prova que o pedido veio da Cloudflare, mas não que veio da **nossa** conta. Para ter essa garantia, use um certificado próprio da zona.
3. **Por que fazer as duas coisas.** Só com o firewall, alguém pode criar outra conta na Cloudflare apontando para o nosso IP e passar por fora das nossas regras de WAF. Nesse caso o `CF-Connecting-IP` continua verdadeiro, porque é a Cloudflare que escreve, mas as regras deste guia não valem para ele.
4. Se o IP do servidor já ficou público antes (DNS com nuvem cinza, por exemplo), pense em trocar o IP. Existem sites que guardam o histórico de DNS.

### Opção C: hospedagem gerenciada (Render, Railway e parecidos)

O plano antigo do projeto (`projeto-fluxo/PROJETO.md`) era a API no Render. Nesses serviços não dá para mexer no firewall, e o endereço próprio do serviço (por exemplo `alera.onrender.com`) **continua aberto** para qualquer um.

O que dá para fazer é um **cabeçalho secreto**:

1. Gere um valor longo e aleatório, por exemplo com `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
2. No painel, vá em Regras > Transform Rules > Modificar cabeçalho do pedido (Modify Request Header). Crie uma regra para `http.host eq "api.SEU-DOMINIO.com.br"` com **Definir valor estático** (Set static): cabeçalho `X-Alera-Borda` e, como valor, o segredo.
3. O Django recusa todo pedido sem esse cabeçalho certo, comparando de forma segura, e só então confia no `CF-Connecting-IP`. Quem implementa é o agente do Django. O segredo fica numa variável de ambiente, nunca no código.

Essa opção é mais fraca que o Tunnel: se o segredo vazar, troque o valor nos dois lugares.

### Teste: a origem está mesmo fechada?

De um computador fora do servidor, tente abrir a API **sem** passar pela Cloudflare: pelo IP do servidor, pelo endereço `*.onrender.com` ou pela porta `8000`. Tem que **falhar** (sem resposta, ou recusado pela regra do cabeçalho secreto). Só depois disso ligue a variável do `CF-Connecting-IP`.

---

## 4. WAF: o porteiro

Menu **Segurança > WAF** (Security > WAF).

### Regras gerenciadas (prontas da Cloudflare)

- **Plano Free:** confira se o **Cloudflare Free Managed Ruleset** está ligado. Ele cobre falhas graves e conhecidas, que a própria Cloudflare atualiza.
- **Plano Pro ou maior:** ligue o **Cloudflare Managed Ruleset**. O **OWASP Core Ruleset** é mais desconfiado e pode barrar pedidos legítimos da API. Ligue com sensibilidade baixa e acompanhe os eventos.

### Regras próprias (Custom rules)

O plano Free permite **5 regras**. Seguem 4 prontas, na ordem em que devem ficar (de cima para baixo). Em "Editar expressão" (Edit expression), cole o texto, troque o domínio e escolha a ação.

**Regra 1: API só responde nos caminhos que existem**

```
(http.host eq "api.SEU-DOMINIO.com.br" and not starts_with(http.request.uri.path, "/api/") and not starts_with(http.request.uri.path, "/admin") and not starts_with(http.request.uri.path, "/static/"))
```

Ação: **Bloquear** (Block). Robôs vivem testando endereços como `/wp-login.php` e `/.env`. Esta regra barra tudo que não é `/api/`, `/admin/` ou `/static/` (o CSS do painel do Django) antes de chegar no servidor.

**Regra 2: API só aceita os métodos que o app usa**

```
(http.host eq "api.SEU-DOMINIO.com.br" and not (http.request.method in {"GET" "HEAD" "POST" "PATCH" "DELETE" "OPTIONS"}))
```

Ação: **Bloquear**. O front-end só usa GET, POST, PATCH e DELETE. O OPTIONS é a "pergunta prévia" que o navegador faz antes de chamar outro domínio (CORS), e o HEAD é usado por monitores. Métodos como `PUT`, `TRACE` e `CONNECT` ficam de fora. Se um dia o app usar `PUT`, acrescente na lista.

**Regra 3: API sem identificação do navegador**

```
(http.host eq "api.SEU-DOMINIO.com.br" and http.user_agent eq "")
```

Ação: **Bloquear**. Todo navegador manda o cabeçalho `User-Agent`, que diz qual navegador é. Pedido sem ele quase sempre é script ou robô mal-feito. Não pega robô esperto, que inventa um `User-Agent`, mas tira muito lixo.

**Regra 4: painéis administrativos acessados de fora do Brasil**

```
(ip.src.country ne "BR" and ((http.host eq "api.SEU-DOMINIO.com.br" and starts_with(http.request.uri.path, "/admin")) or (http.host eq "SEU-DOMINIO.com.br" and starts_with(http.request.uri.path, "/app/admin"))))
```

Ação: **Desafio gerenciado** (Managed Challenge). Vale para o `/admin/` do Django (na API) e para a página do painel da equipe (`/app/admin`, no site). A equipe está no Brasil. Quem acessa de fora (incluindo a rede Tor) precisa passar por uma verificação de "não sou robô". Não é bloqueio: um membro da equipe viajando consegue passar.

Não use desafio nas rotas `/api/...`. Quem chama a API é o JavaScript (`fetch`), e ele não consegue resolver o desafio. Para o morador, apareceria só "não foi possível conectar".

**Vaga 5:** deixe livre para emergências, por exemplo bloquear um IP que esteja atacando.

### Mais forte para o `/admin/` do Django: Cloudflare Access

O Access coloca um login da Cloudflare **antes** do login do Django: a pessoa recebe um código por e-mail. É grátis até 50 usuários.

1. No painel Zero Trust, vá em Acesso > Aplicativos > Adicionar > **Self-hosted**.
2. Domínio `api.SEU-DOMINIO.com.br`, caminho `admin`.
3. Política: **Permitir** (Allow) só os e-mails da equipe. Método de login: **One-time PIN**.

Não coloque o Access em `/api/`. O app do morador quebraria, pelo mesmo motivo do desafio.

### Onde ver o que foi barrado

Em **Segurança > Eventos** (Security > Events). Olhe nos primeiros dias para ver se alguma regra barra gente de verdade.

---

## 5. Limite de tentativas (Rate limiting)

Menu Segurança > WAF > **Regras de limitação de taxa** (Rate limiting rules).

O Django já tem limites próprios: 10 logins por minuto, 20 cadastros por hora e um limite para a renovação da sessão. A regra da borda é a **primeira barreira**: segura enxurradas de pedidos antes que elas cheguem ao servidor. Por isso ela é um pouco mais folgada que a do Django.

### Plano Free (1 regra, janela de 10 segundos)

No Free, a regra só pode olhar o **caminho**, conta por IP, a janela é de 10 segundos e o bloqueio dura 10 segundos.

- Nome: `Login, cadastro e renovação`
- Expressão:

  ```
  (http.request.uri.path in {"/api/auth/login/" "/api/auth/cadastro/" "/api/auth/renovar/"})
  ```

- Contar por: **IP**
- Limite: **10 pedidos em 10 segundos**
- Ação: **Bloquear**, por 10 segundos

Detalhes:

- Cada login no navegador pode gerar **2 pedidos**: a "pergunta prévia" (OPTIONS) e o envio de verdade (POST). Os 10 pedidos valem por uns 5 logins em 10 segundos. Para uma pessoa de verdade, sobra.
- A rota `/api/auth/sair/` (sair da conta) também existe. Se quiser, acrescente na lista.
- Se o painel aceitar a função `starts_with` nesta regra, a expressão `starts_with(http.request.uri.path, "/api/auth/")` já cobre as rotas novas de login que surgirem.
- O bloqueio da borda não traz os cabeçalhos de CORS. Por isso, quem for bloqueado vê no app "Não foi possível conectar ao servidor", e não "Muitas tentativas". É esperado e dura 10 segundos.

### Plano Pro (2 regras, janela de até 1 minuto)

- Regra 1: `/api/auth/login/` e `/api/auth/cadastro/`, 20 pedidos por minuto, bloqueio de 5 minutos.
- Regra 2: `/api/auth/renovar/`, 30 pedidos por minuto, bloqueio de 1 minuto.

### Cuidado: muita gente no mesmo IP

As operadoras de celular colocam **muitas pessoas atrás do mesmo IP** (o nome técnico é CGNAT). Num dia de chuva forte, muita gente de Juiz de Fora pode entrar no app ao mesmo tempo, pela mesma operadora. Por isso:

- não aperte demais os números;
- prefira bloqueios curtos;
- no dia a dia, olhe em Segurança > Eventos se o limite pega gente de verdade.

Quem já está logado continua recebendo os alertas, porque o limite só vale para entrar, cadastrar e renovar a sessão.

---

## 6. Robôs: Bot Fight Mode e Turnstile

### Bot Fight Mode

Fica em **Segurança > Bots** (Security > Bots). É grátis e desafia robôs conhecidos no domínio todo.

Antes de ligar, saiba:

- **Não dá para abrir exceção**: nenhuma regra do WAF pula o Bot Fight Mode. A própria Cloudflare avisa que ele **pode desafiar o tráfego de API**. Se ele desafiar o `fetch` de um morador de verdade, o app falha para essa pessoa.
- Ele coloca um pequeno script na página. Como a nossa CSP não aceita script escrito no HTML, pode aparecer no Console um erro de CSP sobre ele. Não quebra o site: só essa detecção por JavaScript deixa de funcionar.

Recomendação: **ligue e acompanhe por uma semana** em Segurança > Eventos. Se aparecerem desafios em `/api/` para gente de verdade, **desligue** e fique com o limite de tentativas mais o Turnstile.

### Turnstile no cadastro e no login: só o plano, sem implementar

O Turnstile é o "não sou robô" da Cloudflare. Na maioria das vezes ele nem pede clique. O navegador recebe um **token** (um comprovante) e o Django confere esse token com a Cloudflare antes de aceitar o login ou o cadastro.

**Passo 1. Criar o widget no painel.** No menu Turnstile, clique em "Adicionar widget". Nome `ALERA`, hostname `SEU-DOMINIO.com.br`, modo **Managed**. O painel entrega duas chaves:

- a **Site Key**, que é pública e vai no front-end;
- a **Secret Key**, que é secreta e vai **só** numa variável de ambiente do Django. Nunca no Git, nunca no front-end.

**Passo 2. HTML (`front-end/app/login.html`).**

- No fim do `<body>`, **antes** de `../js/login.js`, carregue o script do Turnstile em modo explícito:

  ```html
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"></script>
  ```

  Não ponha `integrity` (SRI) nem copie esse arquivo para o projeto: a Cloudflare atualiza o script e pede que ele venha sempre desse endereço.
- Dentro de cada formulário, logo antes do botão de enviar, uma caixa vazia: `<div id="turnstile-login"></div>` no formulário `data-form="login"` e `<div id="turnstile-cadastro"></div>` no formulário `data-form="cadastro"`.

**Passo 3. JavaScript (`front-end/js/login.js`), sem nada no HTML.**

- Desenhe cada caixa com `turnstile.render('#turnstile-login', { sitekey, action: 'login', language: 'pt-br' })`. Faça o mesmo com `action: 'cadastro'` no outro formulário.
- A `sitekey` pode ficar em `js/api.js`, ao lado do `API_URL`: a de teste quando a página roda no computador, a de verdade no site publicado.
- Ao enviar, pegue o token com `turnstile.getResponse(id)` e mande junto no JSON, por exemplo `{ email, senha, turnstile: token }`.
- Depois de cada resposta, com sucesso ou erro, chame `turnstile.reset(id)`: **cada token vale uma vez só** e dura 5 minutos.
- Se o token estiver vazio, mostre "Confirme que você não é um robô." sem chamar a API.

**Passo 4. CSP.** No fim do `front-end/_headers` já existe o modelo **TURNSTILE**. Ele libera `https://challenges.cloudflare.com` em `script-src` e em `frame-src`, só na página de login. É só tirar os `#` do bloco.

**Passo 5. Django: onde validar.**

- Crie uma função pequena, por exemplo `conferir_turnstile(token, ip, acao)` em `backend/usuarios/turnstile.py`. Ela faz um `POST` para `https://challenges.cloudflare.com/turnstile/v0/siteverify` com `secret` (a Secret Key), `response` (o token) e, se quiser, `remoteip` (o IP de quem acessou, só se o `CF-Connecting-IP` for confiável, seção 3). Dá para usar `urllib.request`, que já é usado em `usuarios/geocodificacao.py`, sem instalar nada novo. Use timeout curto, de 5 segundos.
- Chame a função no começo de `LoginView` e de `CadastroView` (`backend/usuarios/views.py`), **antes** de conferir a senha ou criar a conta. Se não passar, responda `400` com `{"turnstile": "Confirme que você não é um robô."}`.
- Confira na resposta da Cloudflare:
  - `success` é `true`;
  - `hostname` está na lista de domínios esperados;
  - `action` é `login` ou `cadastro`, conforme a rota.

  Recuse token vazio ou com mais de 2.048 caracteres sem nem perguntar à Cloudflare.
- A rota `/api/auth/renovar/` **não** precisa de Turnstile: ela já exige o token de renovação de quem entrou.
- **Decisão da equipe: e se a Cloudflare não responder?** No cadastro, recuse. No login, pense bem: num dia de emergência, recusar trancaria os moradores do lado de fora. Uma saída é aceitar **só** quando a Cloudflare não responder (erro de rede ou timeout), registrar no log e continuar com o limite de tentativas do Django. Se a Cloudflare responder `success: false`, recuse sempre.
- Testes: simule a resposta da Cloudflare (mock do `urlopen`) para os casos de sucesso, falha, token vazio, `action` errada e `hostname` errado.

**Passo 6. Variáveis de ambiente novas.** Coloque só os nomes no `backend/.env.example` e o resto no `backend/README.md`:

| Variável | Uso |
| --- | --- |
| `TURNSTILE_ATIVO` | `true` liga a conferência. Desligado no desenvolvimento, se preferir. |
| `TURNSTILE_SECRET_KEY` | A Secret Key do painel. **Secreta.** |
| `TURNSTILE_HOSTNAMES` | Domínios aceitos no `hostname`, separados por vírgula, por exemplo `SEU-DOMINIO.com.br`. |

**Chaves de teste públicas da Cloudflare**, para o desenvolvimento. Não são segredo e sempre passam:

- Site Key: `1x00000000000000000000AA`
- Secret Key: `1x0000000000000000000000000000000AA`

A chave de produção recusa os tokens de teste. Então não tem como esquecer a de teste ligada em produção sem perceber.

---

## 7. Cache: o que a Cloudflare guarda

### Nunca guardar a API

`/api/me/` devolve os dados pessoais de quem está logado. Se uma resposta dessas ficasse guardada no cache, outra pessoa poderia receber os dados de alguém.

Em **Cache > Cache Rules**, crie a regra:

- Nome: `API nunca em cache`
- Expressão:

  ```
  (http.host eq "api.SEU-DOMINIO.com.br" and (starts_with(http.request.uri.path, "/api/") or starts_with(http.request.uri.path, "/admin")))
  ```

- Ação: **Ignorar cache** (Bypass cache)

Regras do dia a dia:

- **Nunca** use "Cache Everything" ou "Eligible for cache" no host da API.
- O Django também deve mandar `Cache-Control: no-store` nas respostas da API, como segunda proteção (seção 9).

### O site (Cloudflare Pages)

- O Pages **já** guarda o site na borda e troca tudo a cada publicação. A documentação da Cloudflare recomenda **não** criar regras de cache próprias para o Pages: elas podem servir arquivos velhos e atrapalhar redirecionamentos.
- Quanto tempo o **navegador** guarda cada arquivo vem do `_headers`:

  | Arquivos | Tempo | Por quê |
  | --- | --- | --- |
  | HTML | sempre confere | Uma versão nova chega na hora. |
  | Imagens (`/assets/*`) | 30 dias | Quase não mudam. Se trocar uma imagem, troque o nome do arquivo. |
  | CSS e JS | 1 hora | Os nomes não mudam entre versões. Com cache longo, uma correção demoraria dias para chegar. |

  Quando o HTML passar a chamar os arquivos com versão no nome (por exemplo `js/app.js?v=2026-11-06`), o CSS e o JS podem ir para 1 ano. A linha pronta está comentada no `_headers`.
- Em Cache > Configuração (Configuration), deixe **Browser Cache TTL** em **Respeitar os cabeçalhos existentes** (Respect Existing Headers). Senão, a Cloudflare troca os tempos do `_headers`.

### Opcional: CSS do painel do Django

Se o Django servir os arquivos do `/admin/` em `/static/`, eles podem ficar em cache sem risco, porque não têm dado pessoal:

- Expressão: `(http.host eq "api.SEU-DOMINIO.com.br" and starts_with(http.request.uri.path, "/static/"))`
- Ação: **Elegível para cache** (Eligible for cache), com TTL de borda de 1 dia

---

## 8. Recursos da Cloudflare que mexem na página

Alguns botões do painel injetam scripts no HTML e brigam com a CSP:

| Recurso | O que fazer |
| --- | --- |
| **Rocket Loader** (Velocidade > Otimização) | **Desligado.** Ele reescreve os `<script>` e quebra a CSP e o SRI do Leaflet. |
| **Web Analytics** com instalação automática | Ele carrega um script de `static.cloudflareinsights.com`, que a CSP bloqueia. Para usar, peça antes para liberar o domínio na CSP. |
| **Zaraz** | **Desligado.** Injeta script dentro do HTML. |
| **Email Address Obfuscation** | Pode ficar. O script dele vem do próprio site (`/cdn-cgi/...`), e a CSP aceita. |

---

## 9. O que o Django precisa ter (para quem cuida do back-end)

Isto não se configura no painel da Cloudflare, mas sem isto a borda não fecha:

- `DJANGO_ALLOWED_HOSTS=api.SEU-DOMINIO.com.br`
- `CORS_ALLOWED_ORIGINS=https://SEU-DOMINIO.com.br`. Em produção, sem `null` e sem `localhost`. Se quiser testar pelas prévias do Pages, inclua o endereço da prévia só durante o teste.
- A variável que faz o Django ler o `CF-Connecting-IP`: **ligada só depois** da seção 3, e **obrigatória** com o Tunnel.
- O `/admin/` do Django atrás do Tunnel recebe os pedidos como `http` interno. O navegador, porém, manda `Origin: https://api.SEU-DOMINIO.com.br`. Para o login do painel não dar erro de CSRF, `CSRF_TRUSTED_ORIGINS` precisa ter `https://api.SEU-DOMINIO.com.br`. Confiar no cabeçalho `X-Forwarded-Proto` (`SECURE_PROXY_SSL_HEADER`) só é seguro com a origem fechada, pelo mesmo motivo do `CF-Connecting-IP`.
- `Cache-Control: no-store` nas respostas da API.
- Os cabeçalhos de segurança da API (`nosniff`, `X-Frame-Options`, `Referrer-Policy`) vêm do `SecurityMiddleware` do Django. O `_headers` só vale para o site.

---

## 10. Checklist para a equipe marcar

**Front-end (Pages)**

- [ ] Projeto do Pages com pasta de saída `front-end` e sem comando de build
- [ ] Domínio `SEU-DOMINIO.com.br` ligado ao Pages
- [ ] Prévias do Pages protegidas pela política de acesso
- [ ] `connect-src` do `_headers` e `API_URL` do `js/api.js` com o endereço real da API
- [ ] `<script>` da guarda tirado do `<head>` de `app.html` e `admin.html` e posto em arquivo `.js`
- [ ] Prévia testada: Console sem erros de CSP no site, no login, no app e no painel (com mapa)
- [ ] Cabeçalhos conferidos na aba Rede do DevTools

**SSL/TLS**

- [ ] Modo **Full (strict)**
- [ ] **Always Use HTTPS** ligado
- [ ] **TLS mínimo 1.2** e TLS 1.3 ligado
- [ ] `https` funcionando no site e na API (antes do HSTS)
- [ ] **HSTS** ligado: 6 meses, subdomínios, sem preload

**Origem do Django**

- [ ] DNS do `api` com a nuvem laranja
- [ ] Tunnel (opção A) **ou** firewall com IPs da Cloudflare mais Authenticated Origin Pulls (B) **ou** cabeçalho secreto (C)
- [ ] Django escutando só em `127.0.0.1` (opção A)
- [ ] Token do Tunnel e segredos fora do Git
- [ ] Teste feito: a API **não** abre por fora da Cloudflare
- [ ] Só então: variável do `CF-Connecting-IP` ligada

**WAF e limites**

- [ ] Cloudflare Free Managed Ruleset ligado (ou o Managed Ruleset no Pro)
- [ ] Regra 1: só caminhos que existem na API
- [ ] Regra 2: só métodos usados
- [ ] Regra 3: sem `User-Agent` bloqueado
- [ ] Regra 4: painéis de fora do Brasil com desafio
- [ ] (Recomendado) Cloudflare Access no `/admin/` do Django
- [ ] Rate limiting de login, cadastro e renovação
- [ ] Bot Fight Mode ligado e acompanhado por uma semana em Segurança > Eventos

**Cache e outros**

- [ ] Cache Rule "API nunca em cache"
- [ ] Browser Cache TTL em "Respect Existing Headers"
- [ ] Rocket Loader e Zaraz desligados
- [ ] Django com `ALLOWED_HOSTS`, CORS e `CSRF_TRUSTED_ORIGINS` de produção

**Depois (quando for implementar)**

- [ ] Turnstile: widget criado, `TURNSTILE_*` no ambiente, validação no Django com testes, modelo da CSP ligado no `_headers`

---

## Fontes (documentação oficial)

- Cabeçalhos do Pages (`_headers`): <https://developers.cloudflare.com/pages/configuration/headers/>
- Cache no Pages: <https://developers.cloudflare.com/pages/configuration/serving-pages/>
- Regras do WAF: <https://developers.cloudflare.com/waf/custom-rules/>
- Rate limiting e limites por plano: <https://developers.cloudflare.com/waf/rate-limiting-rules/>
- Regras gerenciadas: <https://developers.cloudflare.com/waf/managed-rules/>
- Bot Fight Mode: <https://developers.cloudflare.com/bots/get-started/bot-fight-mode/>
- Authenticated Origin Pulls: <https://developers.cloudflare.com/ssl/origin-configuration/authenticated-origin-pull/>
- Turnstile, validação no servidor: <https://developers.cloudflare.com/turnstile/get-started/server-side-validation/>
- Turnstile e CSP: <https://developers.cloudflare.com/turnstile/reference/content-security-policy/>
- Turnstile, chaves de teste: <https://developers.cloudflare.com/turnstile/troubleshooting/testing/>
- Campo `ip.src.country`: <https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/ip.src.country/>
- Regras de uso dos mapas do OpenStreetMap (exigem o `Referer`): <https://operations.osmfoundation.org/policies/tiles/>
