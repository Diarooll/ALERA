# ALERA · Direção visual "Software calmo" (substitui "Cartaz de rua")

Novembro de 2026. O dono do projeto viu o "Cartaz de rua" e não gostou: muito grande, pouca informação por tela, cara de notícia dramática. Esta é a direção nova. Onde `cartaz-de-rua.md` brigar com este arquivo, vale este.

## O que o dono pediu (palavras dele, resumidas)

- **Mais informação por tela.** Página mais compacta. Textos informativos para quem visita entender a proposta.
- **Fonte menor** em geral (font-size). Nada de manchete gigante, número que ocupa a tela ou seção de tela cheia.
- **Menos drama.** É um site com informação, não uma notícia. O "65" e o "O que ficou depois" não precisam daquele tamanho.
- **Mais suave:** letra arredondada (Plus Jakarta Sans nos títulos), bordas redondas, botões em pílula.
- **Cores:** o azul-noite (`--cor-primaria`) é a cor principal do ALERA. O laranja (`--cor-brilho`) entra só como brilho: um detalhe, um botão, um traço. Fundo claro com branco e bege (`--cor-bege`). Nada de tela inteira laranja.
- **"Modernidade de software":** cara de produto digital bem feito (cartões, grade organizada, hierarquia clara).
- **Animações sempre ligadas**, mesmo com "menos movimento" no sistema (já feito em `movimento.js`/`movimento.css`). Animações suaves, nunca exageradas.

## O que FICA (ele gostou)

- A **chuva no canvas** que muda conforme o nível de perigo.
- As **fotos reais** de Juiz de Fora (com crédito).
- A **coisa viva**: digitar a rua e ver a mensagem de WhatsApp do nível escolhido.
- No app: a tabela de **missões** e as **animações do ranking**.
- O modo escuro.

## Tokens (já trocados em `css/tokens.css`)

- `--fonte-titulo`: Plus Jakarta Sans (peso `--peso-titulo` 800; use 700 em títulos menores). `--fonte-texto`: Source Sans 3.
- Tamanhos grandes compactos: `--fs-cartaz` (título do topo, até 54px), `--fs-numero` (número de destaque, até 52px), `--fs-secao` (título de seção, até 34px). Texto corrido 16 a 18px.
- Cantos: `--raio` 12px, `--raio-card` 16px, `--raio-campo` 10px, `--raio-botao` 999px (pílula).
- Sombras suaves: `--sombra-card` em cartões, `--sombra-forte`/`--sombra-flutua` no que flutua.
- Cores novas: `--cor-brilho` (laranja de detalhe), `--cor-bege` (fundo de bloco claro).

## Regras que continuam valendo

- As da seção **Segurança** de `cartaz-de-rua.md` (textContent, sem `style=`/script inline, `method="post" novalidate`, `rel="noopener noreferrer"`, nenhum domínio externo novo).
- A seção **Sessão** de `cartaz-de-rua.md` (funções do `api.js`, `guarda.js` no head, `#login-manter`).
- `movimento.css`/`movimento.js` e `tema.js` continuam sendo a base de animação e tema.
- Sem emoji como ícone, sem gradiente roxo, sem texto em cinza claro ilegível. Contraste AA.
