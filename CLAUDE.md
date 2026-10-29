# ALERA · site (Front-End Design, Sprint 1)

## Quem mexe em quê
- **Diego** mexe SOMENTE na pasta `site/` (e em `css/site.css`), na branch `diego-site`.
- **Victor** mexe SOMENTE na pasta `app/` (e em `css/app.css`), na branch `victor-app`.
- `css/tokens.css` é compartilhado: não alterar sem avisar o outro.
- Se você é o Claude do Diego, não edite `app/`. Se é o Claude do Victor, não edite `site/`.
- Os arquivos usam `../css/...` porque ficam dentro de `site/` e `app/`.

## O projeto
ALERA = Acompanhamento Local de Emergências e Riscos Ambientais. Slogan: "ALERA no lugar certo, na hora certa".
Projeto do grupo MonkeyNerds (FIAP, Challenge 2026 com a consultoria N/ Lugares Futuros).
Problema: chuvas em Juiz de Fora (MG), alagamentos e deslizamentos em áreas de risco.

Solução:
- Fase 1 (sem hardware): morador se cadastra com telefone + rua e recebe alerta no WhatsApp, gerado por IA a partir de APIs de clima. O alerta traz nível de risco, orientação ("evite esta rua") e abrigo/rota segura.
- Fase 2: hardware instalado aos poucos: Sensor ALERA (encosta, deslizamento) e Bueiro ALERA (nível de água/entupimento).
- Gamificação: avatar, missões (limpar bueiro, reportar lixo, plantar muda na encosta, salvar abrigo), pontos e ranking comunitário POR RUA.
- Usuários: morador de área de risco (celular, pressa, internet ruim) e gestor da Defesa Civil (painel).
- 4 níveis de risco, sempre os mesmos em tudo: NORMAL, ATENÇÃO, ALERTA, EMERGÊNCIA.

Dados usados no pitch (conferir fonte antes de publicar no site): enchentes de fev/2026 em Juiz de Fora com 60+ mortes e 8.854 desabrigados; 128 mil pessoas em área de risco; 142 áreas de risco; 250 t de lixo retiradas dos bueiros. NÃO colocar valores em reais (a banca pediu para tirar).

## O que estamos construindo
Dois HTML que formam um produto só, ligados por link:
- `index.html` (EU): site que apresenta a ideia.
- `app.html` (MEU AMIGO): prévia de como seria o aplicativo. Não mexer nele sem eu pedir.

Seções do `index.html`, nesta ordem:
1. Header: logo "ALERA" + navegação (O problema, Como funciona, Gamificação, Ver o app).
2. Hero: proposta em uma frase + botões "Ver o app" (link para `app.html`) e "Como funciona".
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
  css/tokens.css   ← COMPARTILHADO, não alterar sem avisar
  css/site.css     ← estilos do index.html
  css/app.css      ← estilos do app.html (do meu amigo)
  index.html
  app.html
  ```
- No `<head>`: `css/tokens.css` SEMPRE antes de `css/site.css`.
- Toda cor, fonte, tamanho, espaçamento, raio e sombra vem de `var(--token)` do `tokens.css`. Nunca escrever hex, px de fonte ou font-family direto no `site.css`.
- Nível de risco: sempre cor + palavra escrita (nunca só cor). Usar o par `--cor-risco-X` (fundo) com `--cor-risco-X-texto` (texto).
- `--cor-destaque` é só para gamificação (pontos, progresso).
- Mobile first, sem rolagem horizontal. Área de toque mínima `var(--toque-min)`. Foco visível com `var(--foco)`.
- HTML semântico (header, nav, main, section, footer), `lang="pt-BR"`, textos em português.
- Classes em português e descritivas (`.hero`, `.passo`, `.card-alerta`).

## Contexto da entrega (por que isso importa)
Avaliação de Front-End Design: moodboard e análise crítica, funcionalidades e fluxos, tokens (tipografia, cores com contraste AA, sombras, radius, espaçamentos) e no mínimo 3 componentes em HTML/CSS com as escolhas de design aplicadas. Cada decisão precisa ser justificável pelo contexto do usuário (morador com pressa, no celular, debaixo de chuva). Prefira o simples e legível ao enfeitado.
