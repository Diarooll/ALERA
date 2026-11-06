# Zonas de risco no mapa e alertas de verdade

Combinado com o Diego em 05/11/2026, na branch `feat/zonas-e-abrigos-no-mapa`.

## Por quê

A área de risco hoje é só um nome no `/admin/` do Django, ligada ao morador pelo bairro, e o alerta do painel ALERA é uma simulação. A Defesa Civil precisa desenhar no mapa onde está o risco e soltar o alerta para quem mora ali.

## O que muda

**Área de risco** tem nome, nível e várias **bolinhas** (centro + raio em metros). Juntas, as bolinhas desenham o formato da área.

**Painel ALERA (ADMzão e ADMzinho)**

- Aba nova **Áreas de risco**: mapa para criar a área (nome), pôr bolinhas clicando no mapa, arrastar, mudar o tamanho e apagar. Também renomeia e apaga a área. Daqui não sai alerta.
- Aba **Alertas**: mapa com as áreas pintadas na cor do nível. O admin clica nas áreas para selecionar (uma ou várias), escolhe o nível, escreve a orientação e emite. Muda o nível no servidor e grava no histórico, com quem emitiu e a mensagem. "Últimos alertas" vem do servidor.

**`/admin/` do Django**: "Áreas de risco" sai do menu. Previsões e histórico continuam só leitura.

**Morador**

- O nível vem da **posição da casa**: vale a área cuja bolinha contém a casa. Se a casa está em mais de uma área, vale o **nível mais grave**. Fora de todas, Normal.
- Sem ponto da casa no mapa: o app pede para marcar e avisa que sem isso não recebe os alertas da região.
- Mensagem personalizada: a orientação escrita pelo admin + o abrigo salvo do morador (nome, distância, rota). Sem abrigo salvo, mostra o abrigo aberto mais perto.
- O morador não vê as bolinhas.

## Fora desta etapa

- Bot de WhatsApp (o cálculo de "quem está dentro da área" já fica pronto para ele).
- Script de previsão do tempo.
- Outros erros do app (branch de correções depois).

## Decisões técnicas (do Claude)

- Bolinhas em SQLite: latitude, longitude e raio. Dentro ou fora é conta de distância (haversine), sem PostGIS.
- Raio de 50 m a 3 km; bolinha nova nasce com 200 m.
- Salvar a área manda as bolinhas todas juntas e substitui as antigas.
- Área com histórico de alertas não pode ser apagada (o histórico guarda quem emitiu).
- Emitir de novo o mesmo nível com outra orientação atualiza a mensagem e entra no histórico.
- O vínculo bairro → área deixa de ser usado; o campo fica parado no banco.
