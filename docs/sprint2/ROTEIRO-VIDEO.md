# Roteiro do vídeo da Sprint 2 (até 3 minutos)

**Antes de gravar**

- Abra o **protótipo publicado** (não o arquivo local) numa janela anônima, em tela cheia, com zoom de 100%.
- Na tela de login, deixe o bloco "Modo demonstração" visível.
- Grave com o OBS ou o Clipchamp, em 1080p. Suba no YouTube como **Não listado** (ou no Google Drive com "Qualquer pessoa com o link").
- Teste o link do vídeo na janela anônima antes de pôr no PDF.

| Tempo | O que aparece na tela | O que falar |
| --- | --- | --- |
| 0:00–0:15 | Site (`site.html`), rolando do topo até "Quatro níveis, quatro cores" | "Este é o ALERA, do grupo MonkeyNerds. Ele avisa o morador de Juiz de Fora sobre o risco de chuva na rua dele e mostra o abrigo mais perto." |
| 0:15–0:45 | **Fluxo 2, Criar conta.** Clica em Testar o app → Criar conta. Preenche a etapa 1 deixando o e-mail errado para mostrar o erro, corrige, vai para a etapa 2 e digita o CEP 36010-002 (a rua chega sozinha) | "O primeiro fluxo é o cadastro, em três etapas. O erro aparece embaixo do campo, e o CEP preenche a rua sozinho." (Pare na etapa 3: no protótipo publicado não há servidor para criar a conta) |
| 0:45–1:30 | **Fluxo 1, principal.** Volta ao login → Entrar como morador. Mostra o Alerta → Escolher meu abrigo → seleção "Mostrar: só os que recebem gente agora" → Ver no mapa → Salvar este abrigo (+10 pontos) → Ver rota segura | "O fluxo principal: o morador vê o nível da rua, escolhe o abrigo e abre a rota segura. Salvar o abrigo também conclui uma missão." |
| 1:30–2:10 | **Navegação só pelo teclado.** Tire a mão do mouse e diga isso. Use `Tab` para andar pelo menu (Alerta, Missões, Ranking, Meus dados), `Enter` para abrir Meus dados, `Tab` até o CEP, digite um CEP, `Tab` até Salvar e `Enter` | "Agora só com o teclado: o contorno de foco mostra onde estou, e tudo funciona com Tab e Enter." |
| 2:10–2:40 | **Fluxo 3, Defesa Civil.** Sair → Entrar como admin → Alertas → marca Encosta do Centro → PERIGO → Enviar alerta → confirmar → Ver app | "A Defesa Civil escolhe a área e o nível, confere como o morador vê e confirma. O app do morador já mostra Perigo." |
| 2:40–3:00 | **Vitrine** (`app/componentes.html`), rolando pelos 5 componentes; passa o mouse num botão e clica em "Salvar" para mostrar o erro | "Os cinco componentes do fluxo principal, cada um com os seis estados: default, hover, focus, active, disabled e error." |

**Dicas**

- Fale devagar: 3 minutos passam rápido. Se estourar, corte o trecho do site (0:00–0:15).
- Para o trecho de teclado, deixe o mouse parado num canto da tela.
- Se o mapa demorar a carregar, espere um segundo antes de clicar.
