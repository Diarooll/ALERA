# ALERA · site (Front-End Design, Sprint 1)

## Quem mexe em quê
- **Diego** mexe SOMENTE no site (`codigo/index.html` e `codigo/css/site.css`), na branch `diego-site`.
- **Victor** mexe SOMENTE no app (`codigo/app/` e `codigo/css/app.css`), na branch `victor-app`.
- `codigo/css/tokens.css` é compartilhado: não alterar sem avisar o outro.
- Se você é o Claude do Diego, não edite `codigo/app/`. Se é o Claude do Victor, não edite o site.
- Caminhos: o site (`codigo/index.html`) usa `css/...`, `img/...` e `app/index.html`; o app (`codigo/app/index.html`) usa `../css/...` e volta pro site com `../index.html`.

## O projeto
ALERA = Acompanhamento Local de Emergências e Riscos Ambientais. Slogan: "ALERA no lugar certo, na hora certa".
Projeto do grupo MonkeyNerds (FIAP, Challenge 2026 com a consultoria N/ Lugares Futuros).
Problema: chuvas em Juiz de Fora (MG), alagamentos e deslizamentos em áreas de risco.

Solução:
- Fase 1 (sem hardware): morador se cadastra com telefone + rua e recebe alerta no WhatsApp, gerado por IA a partir de APIs de clima. O alerta traz nível de risco, orientação ("evite esta rua") e abrigo/rota segura.
- Fase 2: hardware instalado aos poucos: Sensor ALERA (encosta, deslizamento) e Bueiro ALERA (nível de água/entupimento).
- Gamificação: avatar, missões (limpar bueiro, reportar lixo, plantar muda na encosta, salvar abrigo), pontos e ranking comunitário POR RUA.
- Usuário: só o morador de área de risco (celular, pressa, internet ruim), que recebe os alertas.
- 4 níveis de risco, sempre os mesmos em tudo: NORMAL, ATENÇÃO, ALERTA, PERIGO. (No `tokens.css` o 4º ainda se chama `--cor-risco-emergencia`; é o mesmo nível.)

Dados usados no pitch (conferir fonte antes de publicar no site): enchentes de fev/2026 em Juiz de Fora com 65 mortes (Polícia Civil, via DGABC) e 8.854 desabrigados; 128 mil pessoas em área de risco (Cemaden, via Estado de Minas); 142 áreas de risco; 250 t de lixo tiradas dos bueiros de jan. a nov. de 2025 (as 35 t da Acessa.com são só de novembro). A Fase 1 se chama "ALERA Web". Logo: gota de pixels com "!" vazado (SVG `#logo-gota` no codigo/index.html). Pontos e ranking da gamificação são simulados. As fotos do site não são de Juiz de Fora (ilustrativas). NÃO colocar valores em reais (a banca pediu para tirar).

## O que estamos construindo
Dois HTML que formam um produto só, ligados por link:
- `codigo/index.html` (EU): site que apresenta a ideia.
- `codigo/app/index.html` (MEU AMIGO): prévia de como seria o aplicativo. Não mexer nele sem eu pedir.

Seções do `index.html`, nesta ordem:
1. Header: logo "ALERA" + navegação (O problema, Como funciona, Gamificação, Testar o app).
2. Hero: proposta em uma frase + botões "Testar o app" (link para `app/index.html`) e "Como funciona".
3. O problema: Juiz de Fora, números acima em destaque.
4. Como funciona: 3 passos da Fase 1 (cadastro → IA monitora o clima → alerta no WhatsApp) + os 4 níveis de risco.
5. Gamificação: exemplos de missão, pontos e ranking por rua.
6. Hardware (Fase 2): Sensor ALERA e Bueiro ALERA.
7. Quem somos: MonkeyNerds.
8. Footer.

## Regras técnicas
- Só HTML e CSS puros. Sem framework, sem build. JavaScript só se for realmente necessário (ex.: menu mobile).
- Estrutura de pastas:
  ```
  ALERA_FrontEnd_DesignSystem_Sprint1.pdf   ← entrega (design system)
  integrantes.txt                           ← entrega (grupo e RMs)
  codigo/
    index.html          ← site (Diego)
    app/index.html      ← prévia do app (Victor)
    css/tokens.css      ← COMPARTILHADO, não alterar sem avisar
    css/site.css        ← estilos do site
    css/app.css         ← estilos do app
    img/                ← fotos do site
    referencias/        ← PowerPoint e logo original (fora do git)
  ```
- No `<head>`: `css/tokens.css` SEMPRE antes de `css/site.css`.
- Toda cor, fonte, tamanho, espaçamento, raio e sombra vem de `var(--token)` do `tokens.css`. Nunca escrever hex, px de fonte ou font-family direto no `site.css`.
- Nível de risco: sempre cor + palavra escrita (nunca só cor). Usar o par `--cor-risco-X` (fundo) com `--cor-risco-X-texto` (texto).
- `--cor-destaque` é só para gamificação (pontos, progresso).
- Modo escuro: checkbox `#tema` (botão sol/lua do topo, sem JS). No site, o `site.css` faz os tokens `--cor-*` apontarem para os `--cor-escuro-*` do `tokens.css` quando o `#tema` está marcado.
- Mobile first, sem rolagem horizontal. Área de toque mínima `var(--toque-min)`. Foco visível com `var(--foco)`.
- HTML semântico (header, nav, main, section, footer), `lang="pt-BR"`, textos em português.
- Classes em português e descritivas (`.hero`, `.passo`, `.card-alerta`).

## Contexto da entrega (por que isso importa)
Avaliação de Front-End Design: moodboard e análise crítica, funcionalidades e fluxos, tokens (tipografia, cores com contraste AA, sombras, radius, espaçamentos) e no mínimo 3 componentes em HTML/CSS com as escolhas de design aplicadas. Cada decisão precisa ser justificável pelo contexto do usuário (morador com pressa, no celular, debaixo de chuva). Prefira o simples e legível ao enfeitado.
