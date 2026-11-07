# ALERA · Direção visual "Cartaz de rua"

Redesenho de novembro de 2026, branch `modificacao-geral`. Este arquivo é a referência de todo o front-end: site, login, app do morador e painel do admin. Se algo aqui brigar com o código antigo, vale este arquivo.

## O que o dono do projeto decidiu

| Pergunta | Decisão |
| --- | --- |
| Direção | Cartaz de rua: blocos de cor chapada, letra condensada enorme, frases curtas e diretas, fotos recortadas e coladas |
| Cores | As mesmas de sempre (`css/tokens.css`). Nenhuma cor nova |
| Manchete do site | **A CHUVA TEM ENDEREÇO** |
| Animação | Muita, mas toda desligável por quem pede menos movimento |
| Fotos | Fotos reais de Juiz de Fora e de chuva, de acervos abertos, com crédito no rodapé, além das 2 atuais |
| App e painel | Cartaz calmo: mesma fonte e cores chapadas, nível de risco gigante no topo do app; o resto organizado para trabalhar |
| Cantos | Quase retos: 4px em tudo (`--raio`) |
| Cadastro | Em 3 etapas: Conta, Endereço, Confirmar, com barra de progresso |
| 65 mortes | Número gigante e parado, em vermelho, sem contagem animada, com a fonte do dado embaixo |
| Modo escuro | Fica no site e no app (e no painel) |

## A ideia

> No ALERA, **os quatro níveis do alerta (verde, amarelo, laranja, vermelho)** viram **campos inteiros de cor chapada que a página atravessa**, e **o nome da rua de quem visita** vira **a manchete**.

O teste do concorrente: troque ALERA por "um app de previsão do tempo". A frase não funciona: previsão do tempo não tem nível de risco por rua nem fala o nome da sua rua. Então a ideia é do ALERA.

**A coisa viva do site:** a pessoa digita o nome da rua dela e escolhe um nível. A mensagem de alerta aparece como chegaria no WhatsApp, com o nome daquela rua, o que fazer e o abrigo. O campo de cor do topo muda para a cor do nível e a chuva desenhada fica mais forte. Funciona sem servidor (é demonstração) e sem script mostra um exemplo fixo.

## Tipografia

- **Bebas Neue** (`--fonte-titulo`): manchetes, títulos de seção, números grandes, nome do nível de risco. Só caixa alta, um peso só. **Nunca em negrito** (`font-weight` sempre 400) e nunca em texto corrido.
- **Source Sans 3** (`--fonte-texto`): todo o resto. 400 no texto, 600 em destaque, 700 em títulos pequenos do app (cartões, formulários), onde a Bebas ficaria pequena demais para ler.
- Duas famílias no máximo. Nenhuma outra fonte.
- Texto corrido com 16px ou mais e na cor cheia (`--cor-texto`). Cinza (`--cor-texto-suave`) só para nota secundária.
- Tamanhos de cartaz: `--fs-cartaz` (manchete), `--fs-numero` (um número que ocupa a tela), `--fs-secao` (título de seção do site). Bebas com `line-height` entre 0.85 e 0.95.

## Cores (sem mudança)

Base `--cor-primaria` (azul-noite), fundo `--cor-fundo`, superfície branca, texto `--cor-texto`. Os quatro níveis (`--cor-risco-*`) com o texto certo em cima de cada um (`--cor-risco-*-texto`). Modo escuro com os tokens `--cor-escuro-*`.

No cartaz, cada bloco é UMA cor chapada e o texto em cima dele é UMA outra cor. Blocos encostam um no outro. A cor de destaque (`--cor-destaque`) continua só para pontos e progresso da gamificação.

Modo escuro: o `<html>` recebe `data-tema="escuro"` (feito por `js/tema.js`). O CSS escuro usa `:root[data-tema="escuro"]` e pode manter `:root:has(#tema:checked)` para quem está sem script. O botão continua sendo o checkbox `#tema` com o `label for="tema"`.

## Regras da casa (o que deixa com cara de IA)

Valem em todas as páginas. A ferramenta `inspect.mjs` da skill `design-taste-frontend` mede várias delas.

- Títulos com no máximo 2 linhas em qualquer largura (1440, 768 e 390 px). Cortar palavras antes de diminuir a letra.
- Um `h1` por página, e todo bloco que a pessoa veio ver tem um título que diz o que ele é.
- **Proibido:** selo pequeno acima do título ("Fase 1" em cima de "ALERA Web"); letra pequena em caixa alta espaçada; fonte monoespaçada; numeração 01/02/03 decorativa (lista com ordem de verdade usa `<ol>`); linhas finas de divisão e caixas com contorno de 1px (fora de formulário e tabela); gradiente; sombra em coisa parada (só no que flutua: menu aberto, aviso, diálogo, com `--sombra-flutua`); vidro/desfoque; emoji; fileira de cartões iguais com ícone em cima; palavra destacada em outra cor ou itálico dentro da manchete.
- Separar blocos com espaço, troca de cor de fundo ou mudança de escala, nunca com linha ou sombra.
- Margens externas iguais dos dois lados. Nenhum bloco com metade da tela vazia. Nenhum trecho vazio maior que meia tela.
- Botões chapados, uma cor, canto `--raio` (4px). Um formato de botão só no projeto inteiro.
- Fotos com canto reto ou recortadas em forma simples (arco, círculo) com `clip-path`; no máximo 2 ou 3 inclinadas no site inteiro, nunca texto inclinado.
- Textos em português do dia a dia, curtos e concretos, como a Defesa Civil falaria na rua. Sem clichê ("soluções inovadoras", "experiência única"), sem trio de adjetivos, sem travessão em excesso.

## Movimento

Arquivos comuns, já prontos: `css/movimento.css` e `js/movimento.js` (instruções no topo de cada um). Toda página linka `movimento.css` depois de `base.css` e carrega `movimento.js` antes do script da página. `js/tema.js` vai no `<head>`, sem `defer`.

O que existe:

| No HTML | Efeito |
| --- | --- |
| `data-revelar` (ou `="esquerda"`, `"direita"`, `"crescer"`) | sobe e aparece ao entrar na tela |
| `data-revelar-grupo` | os filhos entram um depois do outro (70 ms) |
| `data-obturador` em volta de `<img>` | a foto abre como obturador (uma por página, a principal) |
| `data-ima` | botão puxado de leve pelo mouse (só o botão principal) |
| `data-deriva="0.15"` | foto anda devagar com a rolagem |
| `data-contar` | número conta do zero até o valor escrito. **Nunca em mortes, desabrigados ou vítimas** |
| `class="pressionavel"` | afunda ao apertar e volta com mola |

No JS: `Movimento.observar(raiz)` depois de montar conteúdo novo (listas que vêm do servidor), `Movimento.aviso(texto, { tipo: 'ok' | 'erro' | 'info' })` em vez de `alert()`, `Movimento.tremer(campo)` em erro de formulário, `Movimento.vibrar()` em ação concluída no celular, `Movimento.reduzido()` para saber se deve animar.

Regras:

- Animar só `transform`, `opacity`, `clip-path` e `translate`. Nada de animar largura, altura, margem ou cor de fundo de página inteira (a troca de cor de bloco por rolagem é feita com camadas e opacidade).
- Todo efeito tem versão parada em `@media (prefers-reduced-motion: reduce)`: o conteúdo aparece, só não viaja.
- Nada fica escondido se o script falhar (o `movimento.css` já cuida disso para os atributos acima; efeito novo da página tem que seguir a mesma regra).
- Tempos e curvas só pelos tokens (`--dur-*`, `--curva-*`).

## Segurança (vale para todo HTML e JS novo)

Vindo da auditoria do front-end:

1. Texto do servidor entra por `el.textContent = x` ou criando elementos. Nunca `innerHTML`, `insertAdjacentHTML`, `outerHTML` com dado, nem template string que vira HTML.
2. Leaflet: `bindPopup`, `bindTooltip`, `setContent`, `L.divIcon({ html })` recebem sempre um elemento, nunca string com dado.
3. Mensagem de alerta com quebra de linha: CSS `white-space: pre-line`. Nunca trocar `\n` por `<br>` nem transformar URL do texto em link.
4. Nada de `<script>` inline, `onclick=` ou `style=` no HTML (a CSP vai bloquear). Use classes e arquivos.
5. Formulários: `method="post" novalidate`, com o `preventDefault` no JS. E-mail de cadastro com `autocomplete="username"`, senha nova com `new-password`, senha de login com `current-password`.
6. Todo `target="_blank"` com `rel="noopener noreferrer"`.
7. Nenhum domínio externo novo. Os permitidos: Google Fonts, `cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/`, `tile.openstreetmap.org`, `viacep.com.br`. Fotos e vídeos ficam dentro do projeto (`front-end/assets/`).
8. Dado de outra pessoa nunca vai em `style` nem em `setAttribute('style')`. Classe com o nível (`nivel--alerta`) pode, porque o servidor só aceita os quatro níveis.

## Sessão (login que não cai)

Feito pelo agente de back-end em `js/api.js`. As páginas usam:

- `salvarSessao(dados, manter)`, `lerSessao()`, `limparSessao()`, `sairDaConta()`.
- `chamarApi(rota, { metodo, corpo })` igual a antes, mas renova o login sozinha. Se ela devolver 401, a sessão acabou de verdade.
- `js/guarda.js` no `<head>` do app e do painel, no lugar do script inline antigo. Não remover.
- No login, uma caixinha **"Continuar conectado neste aparelho"**, `id="login-manter"`, marcada por padrão.

## Quem cuida de qual arquivo

| Arquivo | Dono |
| --- | --- |
| `css/tokens.css`, `css/base.css`, `css/movimento.css`, `js/movimento.js`, `js/tema.js`, este documento | orquestrador |
| `index.html`, `css/site.css`, `js/site.js`, `assets/img/`, `assets/video/` | agente do site |
| `app/login.html`, `css/login.css`, `js/login.js` | agente do login |
| `app/app.html`, `css/app.css`, `css/mapa.css`, `js/app.js`, `js/mapa.js`, `js/endereco.js` | agente do app |
| `app/admin.html`, `css/admin.css`, `js/admin.js` | agente do painel |
| `js/api.js`, `js/guarda.js` e os trechos de sessão em `login.js`, `app.js`, `admin.js` | agente de back-end (sessão) |

Quem precisa de mudança num arquivo que não é seu pede ao orquestrador.
