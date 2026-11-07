// Mapa de abrigos (Leaflet + OpenStreetMap), usado no app e no painel.
// Todo texto que vem do servidor entra na tela por textContent, nunca por innerHTML.
// Cuidado com o Leaflet: bindTooltip e bindPopup com texto puro viram HTML. Passe elemento().

const CENTRO_MAPA = [-21.7642, -43.3503] // Juiz de Fora (MG)
const ENDERECO_TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const ATRIBUICAO =
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>'

const SITUACOES = {
  aberto: 'aberto agora',
  poucas: 'poucas vagas',
  'so-alerta': 'abre só em nível de alerta',
  fechado: 'fechado',
}
// Situações em que o abrigo recebe gente agora
const ESTADOS_ABERTOS = ['aberto', 'poucas']

// O abrigo recebe gente no nível de risco de quem consulta? O "só em alerta" abre
// quando o nível chega a alerta ou perigo; antes disso não conta como aberto
function abrigoRecebe(abrigo, nivel) {
  if (ESTADOS_ABERTOS.includes(abrigo.situacao)) return true
  return abrigo.situacao === 'so-alerta' && (nivel === 'alerta' || nivel === 'perigo')
}

function criarMapa(elemento, { centro = CENTRO_MAPA, zoom = 14 } = {}) {
  const mapa = L.map(elemento).setView(centro, zoom)
  L.tileLayer(ENDERECO_TILES, { maxZoom: 19, attribution: ATRIBUICAO }).addTo(mapa)
  adicionarBotaoTemaMapa(mapa)
  return mapa
}

// ---------- Mapa claro ou escuro, separado do tema da página ----------
// Cada mapa ganha um botão no canto. A escolha vale para todos os mapas abertos
// e fica guardada em localStorage.temaMapa ('claro' ou 'escuro'). Sem escolha, claro.
const mapasComTema = []

function lerTemaMapa() {
  try {
    return localStorage.getItem('temaMapa') === 'escuro' ? 'escuro' : 'claro'
  } catch {
    return 'claro'
  }
}

function aplicarTemaMapa(tema) {
  const escuro = tema === 'escuro'
  mapasComTema.forEach(({ mapa, botao }) => {
    mapa.getContainer().classList.toggle('mapa--escuro', escuro)
    botao.setAttribute('aria-pressed', String(escuro))
  })
}

function trocarTemaMapa() {
  const novo = temaMapaAtual === 'escuro' ? 'claro' : 'escuro'
  try {
    localStorage.setItem('temaMapa', novo)
  } catch {
    // Sem armazenamento (aba anônima): troca só nesta visita
  }
  temaMapaAtual = novo
  aplicarTemaMapa(novo)
}

let temaMapaAtual = lerTemaMapa()

// Desenho do botão: lua (mapa escuro). Feito com createElementNS, sem innerHTML
function desenhoLua() {
  const ns = 'http://www.w3.org/2000/svg'
  const svg = document.createElementNS(ns, 'svg')
  svg.setAttribute('viewBox', '0 0 24 24')
  svg.setAttribute('aria-hidden', 'true')
  svg.setAttribute('focusable', 'false')
  svg.setAttribute('class', 'mapa-cor__icone')
  const caminho = document.createElementNS(ns, 'path')
  caminho.setAttribute('d', 'M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z')
  svg.append(caminho)
  return svg
}

function adicionarBotaoTemaMapa(mapa) {
  const ControleTema = L.Control.extend({
    options: { position: 'topright' },
    onAdd() {
      const botao = elemento('button', 'mapa-cor')
      botao.type = 'button'
      botao.title = 'Alternar o mapa entre claro e escuro'
      botao.append(desenhoLua(), elemento('span', 'mapa-cor__texto', 'Mapa escuro'))
      L.DomEvent.disableClickPropagation(botao)
      L.DomEvent.on(botao, 'click', trocarTemaMapa)
      mapasComTema.push({ mapa, botao })
      return botao
    },
  })
  mapa.addControl(new ControleTema())
  aplicarTemaMapa(temaMapaAtual)
}

// Pino de cartaz: uma plaquinha com um número ou uma palavra curta e uma ponta embaixo.
// "classes" muda a cor (pin--fechado, pin--salvo, pin--voce, pin--novo).
// O ícone tem tamanho zero e a plaquinha se posiciona pelo CSS com a ponta no ponto exato,
// assim a placa pode ter a largura do texto ("Casa", "12") sem errar a âncora
function iconePin(texto, classes = '') {
  const pin = document.createElement('span')
  pin.className = `pin ${classes}`.trim()
  pin.append(elemento('span', 'pin__texto', texto))
  return L.divIcon({ html: pin, className: 'pin-caixa', iconSize: [0, 0], iconAnchor: [0, 0] })
}

function formatarDistancia(metros) {
  if (metros == null) return ''
  if (metros < 1000) return `${metros} m`
  return `${(metros / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} km`
}

// "600 m · 8 min a pé · aberto agora"
function resumoAbrigo(abrigo) {
  const partes = []
  if (abrigo.distancia_m != null) {
    partes.push(formatarDistancia(abrigo.distancia_m), `${abrigo.tempo_a_pe_min} min a pé`)
  }
  partes.push(SITUACOES[abrigo.situacao] || abrigo.situacao)
  return partes.join(' · ')
}

function linkGoogleMaps(abrigo) {
  const destino = `${abrigo.latitude},${abrigo.longitude}`
  return `https://www.google.com/maps/dir/?api=1&destination=${destino}&travelmode=walking`
}

// Cria um elemento com texto seguro
function elemento(tag, classe, texto) {
  const el = document.createElement(tag)
  if (classe) el.className = classe
  if (texto !== undefined) el.textContent = texto
  return el
}
