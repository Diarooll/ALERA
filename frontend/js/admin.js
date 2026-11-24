// Painel do administrador.
// Áreas (com as bolinhas), abrigos, tipos e alertas vêm do servidor.
// Emitir alerta muda o nível da área de verdade; o WhatsApp ainda não está ligado.
// Todo texto vindo do servidor entra na tela por textContent (ver elemento() em mapa.js).

const $ = (seletor) => document.querySelector(seletor)

const NIVEIS = {
  normal: {
    nome: 'NORMAL',
    orientacao:
      'Sem chuva forte prevista. Depois de muita chuva o solo ainda pode ceder: viu rachaduras, ligue 199.',
  },
  atencao: {
    nome: 'ATENÇÃO',
    orientacao: 'Chuva prevista para hoje. Confira seu abrigo e tire o lixo da frente do bueiro.',
  },
  alerta: {
    nome: 'ALERTA',
    orientacao: 'Chuva forte prevista em até 24 horas. Evite ruas alagadas e deixe documentos à mão.',
  },
  // O app completa com o abrigo de cada morador: "Vá para o seu abrigo: ..."
  perigo: { nome: 'PERIGO', orientacao: 'Risco agora. Saia de casa.' },
}

const estado = { areas: [], abrigos: [], tipos: [], alertas: [] }

// O Leaflet precisa da cor escrita: lê os valores de tokens.css, que fica como única fonte
const corDoToken = (nome) => getComputedStyle(document.documentElement).getPropertyValue(nome).trim()
const CORES_NIVEL = Object.fromEntries(Object.keys(NIVEIS).map((n) => [n, corDoToken(`--cor-risco-${n}`)]))
const COR_DESENHO = CORES_NIVEL.perigo
const COR_ESCOLHIDA = corDoToken('--cor-primaria')

// Botão Sair: o api.js avisa o servidor (sem travar se ele estiver fora) e só então vai para o login
async function encerrarSessao(evento) {
  evento?.preventDefault()
  await sairDaConta()
  location.replace('login.html')
}

// Só o 401 derruba: a sessão acabou de vez (o api.js já tentou renovar).
// O 403 numa ação (a conta não pode fazer aquilo) cai no aviso de erro de quem chamou
function irParaLogin() {
  limparSessao()
  location.replace('login.html')
}

// Conta que não é de administrador: o lugar dela é o app do morador, sem perder a sessão.
// Guarda o papel, para o login não a mandar de volta para cá
function irParaOApp(papel = 'morador') {
  guardarPapel(papel)
  location.replace('app.html')
}

// O servidor decide quem é administrador. Sem resposta, a pessoa fica e vê o aviso de erro;
// os dados do painel continuam protegidos, porque o servidor só os entrega a administradores.
async function conferirAdministrador() {
  if (modoTesteAtivo()) {
    if (lerSessao()?.papel !== 'admin') location.replace('app.html')
    return
  }

  try {
    const resposta = await chamarApi('/me/')

    if (resposta.status === 401) return irParaLogin()
    if (resposta.ok) {
      const { papel } = await resposta.json()
      if (papel !== 'admin') irParaOApp(papel)
    }
  } catch {
    // sem resposta do servidor: carregarTudo() mostra o aviso
  }
}

$('#sair').addEventListener('click', encerrarSessao)

// pageshow também cobre o botão Voltar, que pode reabrir o painel da memória sem rodar o <head>
window.addEventListener('pageshow', conferirAdministrador)

// ---------- carregar dados ----------

async function pegar(rota) {
  const resposta = await chamarApi(rota)
  if (resposta.status === 401) {
    irParaLogin()
    throw new Error('sessão')
  }
  if (resposta.status === 403) {
    irParaOApp()
    throw new Error('sem permissão')
  }
  if (!resposta.ok) throw new Error(`erro ${resposta.status}`)
  return resposta.json()
}

async function carregarTudo() {
  if (modoTesteAtivo()) {
    mostrarStatus('Modo teste: sem servidor, as áreas e os abrigos reais não carregam.', true)
    $('#painel-apoio').textContent = 'Defesa Civil · modo teste'
    return desenharTudo()
  }

  try {
    ;[estado.areas, estado.abrigos, estado.tipos, estado.alertas] = await Promise.all([
      pegar('/areas/'),
      pegar('/abrigos/'),
      pegar('/tipos-abrigo/'),
      pegar('/alertas/'),
    ])
    mostrarStatus('')
    $('#painel-apoio').textContent = 'Defesa Civil · dados do servidor'
  } catch {
    mostrarStatus('Não foi possível falar com o servidor. Tente de novo em instantes.', true)
    $('#painel-apoio').textContent = 'Defesa Civil · sem conexão'
  }

  desenharTudo()
}

function mostrarStatus(texto, erro = false) {
  const aviso = $('#abrigos-status')
  aviso.textContent = texto
  aviso.hidden = !texto
  aviso.classList.toggle('mapa-aviso--erro', erro)
}

function desenharTudo() {
  desenharAreas()
  desenharHistorico()
  desenharListaAreas()
  desenharTipos()
  desenharListaAbrigos()
  desenharMapas()
  contarAbrigosAbertos()
  atualizarPrevia()
}

// O Leaflet só mede o mapa quando a aba aparece: cada mapa é desenhado na sua aba
function desenharMapas() {
  if (location.hash === '#abrigos') desenharMarcadores()
  if (location.hash === '#areas') desenharMapaAreas()
  if (location.hash === '#alertas') desenharMapaAlertas()
}

function criarMapaSeguro(seletor) {
  if (typeof L === 'undefined') return null // o Leaflet não carregou (sem internet)
  return criarMapa($(seletor), { zoom: 14 })
}

// Bolinha no mapa. Também serve de "área" para clicar
function desenharBolinha(camada, circulo, opcoes) {
  return L.circle([Number(circulo.latitude), Number(circulo.longitude)], {
    radius: circulo.raio_m,
    weight: 2,
    fillOpacity: 0.25,
    ...opcoes,
  }).addTo(camada)
}

// Retângulo que cobre todas as bolinhas (toBounds recebe o lado do quadrado: o dobro do raio)
function limitesDasBolinhas(circulos) {
  return circulos.reduce(
    (limites, c) => limites.extend(L.latLng(Number(c.latitude), Number(c.longitude)).toBounds(2 * c.raio_m)),
    L.latLngBounds([]),
  )
}

function enquadrarBolinhas(mapa, circulos) {
  setTimeout(() => {
    mapa.invalidateSize()
    if (circulos.length) mapa.fitBounds(limitesDasBolinhas(circulos), { padding: [30, 30], maxZoom: 16 })
  }, 50)
}

// Na primeira vez que há bolinhas, enquadra todas; depois respeita o zoom da pessoa.
// Devolve se o mapa já foi enquadrado
function ajustarMapa(mapa, jaEnquadrado) {
  const todas = estado.areas.flatMap((a) => a.circulos)
  if (!jaEnquadrado && todas.length) {
    enquadrarBolinhas(mapa, todas)
    return true
  }
  setTimeout(() => mapa.invalidateSize(), 50)
  return jaEnquadrado
}

// ---------- alertas: escolher as áreas no mapa e emitir de verdade ----------

const form = $('#form-alerta')
const campoMensagem = $('#alerta-mensagem')
const confirmacao = $('#confirmacao')
// Áreas marcadas para receber o alerta (ids). Sobrevive ao recarregar os dados
const escolhidas = new Set()

function nivelEscolhido() {
  return form.elements.nivel.value
}

function areasEscolhidas() {
  return estado.areas.filter((a) => escolhidas.has(a.id))
}

function nomesDasAreas(areas) {
  return areas.map((a) => a.nome).join(', ')
}

function alternarArea(id) {
  if (escolhidas.has(id)) escolhidas.delete(id)
  else escolhidas.add(id)
  desenharListaAlerta()
  desenharMapaAlertas()
  atualizarPrevia()
}

function desenharListaAlerta() {
  const lista = $('#alerta-areas')
  lista.replaceChildren()

  if (!estado.areas.length) {
    lista.append(elemento('li', 'mapa-aviso', 'Nenhuma área ainda. Crie a primeira na aba Áreas de risco.'))
  }

  estado.areas.forEach((area) => {
    const item = elemento('li')
    const rotulo = elemento('label', 'area-item')
    const caixa = elemento('input')
    caixa.type = 'checkbox'
    caixa.checked = escolhidas.has(area.id)
    caixa.addEventListener('change', () => alternarArea(area.id))

    rotulo.append(
      caixa,
      elemento('span', 'area-item__nome', area.nome),
      elemento('span', `etiqueta nivel--${area.nivel}`, NIVEIS[area.nivel].nome),
    )
    item.append(rotulo)
    lista.append(item)
  })
}

let mapaAlertas = null
let camadaAlertas = null
let alertasEnquadrado = false // enquadra as áreas uma vez; depois respeita o zoom da pessoa

function desenharMapaAlertas() {
  if (location.hash !== '#alertas') return
  if (!mapaAlertas) {
    mapaAlertas = criarMapaSeguro('#mapa-alertas')
    if (!mapaAlertas) return
    camadaAlertas = L.layerGroup().addTo(mapaAlertas)
  }

  camadaAlertas.clearLayers()
  estado.areas.forEach((area) => {
    const escolhida = escolhidas.has(area.id)
    const cor = CORES_NIVEL[area.nivel]
    area.circulos.forEach((circulo) => {
      desenharBolinha(camadaAlertas, circulo, {
        color: escolhida ? COR_ESCOLHIDA : cor,
        fillColor: cor,
        weight: escolhida ? 5 : 2,
        fillOpacity: escolhida ? 0.45 : 0.2,
      })
        .bindTooltip(elemento('span', '', `${area.nome} · ${NIVEIS[area.nivel].nome}`))
        .on('click', () => alternarArea(area.id))
    })
  })

  alertasEnquadrado = ajustarMapa(mapaAlertas, alertasEnquadrado)
}

function mensagemAtual() {
  return campoMensagem.value.trim()
}

function desenharAreas() {
  const corpo = $('#tabela-areas')
  corpo.replaceChildren()

  if (!estado.areas.length) {
    const linha = elemento('tr')
    const celula = elemento('td', '', 'Nenhuma área de risco cadastrada ainda.')
    celula.colSpan = 2
    linha.append(celula)
    corpo.append(linha)
  }

  estado.areas.forEach((area) => {
    const linha = elemento('tr')
    const nome = elemento('th', '', area.nome)
    nome.scope = 'row'
    const celula = elemento('td')
    celula.append(elemento('span', `etiqueta nivel--${area.nivel}`, NIVEIS[area.nivel].nome))
    linha.append(nome, celula)
    corpo.append(linha)
  })

  // Área apagada sai da escolha do alerta
  for (const id of escolhidas) {
    if (!estado.areas.some((a) => a.id === id)) escolhidas.delete(id)
  }
  desenharListaAlerta()

  $('#total-areas').textContent = estado.areas.length || '–'
  contarAreasEmRisco()
}

function contarAreasEmRisco() {
  $('#total-risco').textContent = estado.areas.length
    ? estado.areas.filter((a) => ['alerta', 'perigo'].includes(a.nivel)).length
    : '–'
}

function atualizarPrevia() {
  const nivel = NIVEIS[nivelEscolhido()]
  const areas = areasEscolhidas()

  $('#previa-rua').textContent = areas.length ? nomesDasAreas(areas) : 'Escolha uma área'
  $('#previa-selo').className = `selo nivel--${nivelEscolhido()}`
  $('#previa-nivel').textContent = nivel.nome
  // No app, o morador vê a orientação e, embaixo, o abrigo dele
  $('#previa-mensagem').textContent = mensagemAtual()
  const nivelId = nivelEscolhido()
  const comeco = nivelId === 'atencao' ? 'Confira o caminho até o seu abrigo' : 'Vá para o seu abrigo'
  $('#previa-abrigo').textContent =
    nivelId === 'normal' ? '' : `${comeco}: [abrigo de cada morador], a [distância].`
  $('#previa-alcance').textContent = !estado.areas.length
    ? 'Crie uma área na aba Áreas de risco para poder emitir alertas.'
    : areas.length
      ? `Vai para quem mora dentro de: ${nomesDasAreas(areas)}. Cada morador vê também o abrigo dele.`
      : 'Toque nas áreas do mapa ou marque na lista.'
}

function validarMensagem() {
  // required sozinho aceita um texto só de espaços
  campoMensagem.setCustomValidity(mensagemAtual() ? '' : 'Escreva o que o morador deve fazer.')
}

function preencherOrientacao() {
  // Só troca o texto padrão: o que a pessoa escreveu não se perde ao mudar de nível
  const textoPadrao = Object.values(NIVEIS).some((n) => n.orientacao === campoMensagem.value)

  if (textoPadrao || !mensagemAtual()) {
    campoMensagem.value = NIVEIS[nivelEscolhido()].orientacao
    validarMensagem()
  }
}

const ORIGENS = { 'defesa-civil': 'Defesa Civil', previsao: 'previsão do tempo' }

function desenharHistorico() {
  const lista = $('#historico')
  lista.replaceChildren()

  if (!estado.alertas.length) {
    lista.append(elemento('li', 'historico__item mapa-aviso', 'Nenhum alerta emitido ainda.'))
  }

  estado.alertas.forEach((alerta) => {
    const item = elemento('li', 'historico__item')
    const corpo = elemento('div')
    const quando = new Date(alerta.criado_em).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
    const quem = alerta.responsavel || ORIGENS[alerta.origem] || alerta.origem

    corpo.append(elemento('strong', '', alerta.area))
    if (alerta.mensagem) corpo.append(elemento('p', 'historico__texto', alerta.mensagem))
    corpo.append(elemento('p', 'historico__meta', `${quando} · ${quem}`))
    item.append(elemento('span', `etiqueta nivel--${alerta.nivel_novo}`, NIVEIS[alerta.nivel_novo].nome), corpo)
    lista.append(item)
  })
}

async function registrarAlerta() {
  const areas = areasEscolhidas()
  const nivelId = nivelEscolhido()
  $('#alerta-retorno').textContent = 'Enviando…'

  try {
    const resposta = await chamarApi('/alertas/', {
      metodo: 'POST',
      corpo: { areas: areas.map((a) => a.id), nivel: nivelId, mensagem: mensagemAtual() },
    })
    if (resposta.status === 401) return irParaLogin()
    if (!resposta.ok) {
      $('#alerta-retorno').textContent = mensagemDeErro(await resposta.json().catch(() => null))
      return
    }

    const gravados = await resposta.json()
    await carregarTudo()
    $('#alerta-retorno').textContent = gravados.length
      ? `${NIVEIS[nivelId].nome} emitido para ${nomesDasAreas(areas)}. Já aparece no app de quem mora lá.`
      : 'Nada mudou: essas áreas já estavam com esse nível e essa orientação.'
  } catch {
    $('#alerta-retorno').textContent = 'Sem conexão com o servidor. O alerta não foi emitido.'
  }
}

form.addEventListener('change', (evento) => {
  if (evento.target.name === 'nivel') preencherOrientacao()
  atualizarPrevia()
})

campoMensagem.addEventListener('input', () => {
  validarMensagem()
  atualizarPrevia()
})

form.addEventListener('submit', (evento) => {
  evento.preventDefault()

  const areas = areasEscolhidas()
  if (!areas.length) {
    $('#alerta-retorno').textContent = 'Escolha pelo menos uma área no mapa ou na lista.'
    return
  }

  $('#confirmacao-titulo').textContent =
    `Emitir ${NIVEIS[nivelEscolhido()].nome} para quem mora em: ${nomesDasAreas(areas)}?`
  $('#confirmacao-mensagem').textContent = mensagemAtual()

  // Sem isto, fechar com Esc repetiria a resposta da confirmação anterior
  confirmacao.returnValue = ''
  confirmacao.showModal()
})

confirmacao.addEventListener('close', () => {
  if (confirmacao.returnValue === 'enviar') registrarAlerta()
})

// ---------- áreas de risco: desenhar com bolinhas ----------

const RAIO_NOVO_M = 200
const formArea = $('#form-area')
// Área em edição: { id (null se nova), nome, circulos: [{ latitude, longitude, raio_m }] }
let areaEditando = null
let bolinhaEscolhida = null // índice em areaEditando.circulos
let camadaEscolhida = null // desenho da bolinha escolhida: o controle de tamanho mexe só nele
let mapaAreas = null
let camadaOutras = null // áreas que não estão em edição
let camadaEdicao = null
let areasEnquadrado = false

function statusAreas(texto, erro = false) {
  const aviso = $('#areas-status')
  aviso.textContent = texto
  aviso.classList.toggle('mapa-aviso--erro', erro)
}

function desenharListaAreas() {
  const lista = $('#areas-lista')
  lista.replaceChildren()

  if (!estado.areas.length) {
    lista.append(elemento('li', 'mapa-aviso', 'Nenhuma área ainda. Toque em "+ Nova área" para criar a primeira.'))
  }

  estado.areas.forEach((area) => {
    const item = elemento('li')
    const botao = elemento('button', `area-item${areaEditando?.id === area.id ? ' area-item--ativa' : ''}`)
    botao.type = 'button'
    const bolinhas = area.circulos.length === 1 ? '1 bolinha' : `${area.circulos.length} bolinhas`
    botao.append(
      elemento('span', 'area-item__nome', area.nome),
      elemento('span', 'area-item__info', bolinhas),
      elemento('span', `etiqueta nivel--${area.nivel}`, NIVEIS[area.nivel].nome),
    )
    botao.addEventListener('click', () => editarArea(area))
    item.append(botao)
    lista.append(item)
  })
}

function desenharMapaAreas() {
  if (location.hash !== '#areas') return
  if (!mapaAreas) {
    mapaAreas = criarMapaSeguro('#mapa-areas')
    if (!mapaAreas) return statusAreas('O mapa não carregou. Confira a internet e recarregue a página.', true)
    camadaOutras = L.layerGroup().addTo(mapaAreas)
    camadaEdicao = L.layerGroup().addTo(mapaAreas)
    mapaAreas.on('click', (evento) => porBolinha(evento.latlng))
  }

  // As outras áreas ficam claras, para servir de referência ao desenhar
  camadaOutras.clearLayers()
  estado.areas.forEach((area) => {
    if (areaEditando?.id === area.id) return
    area.circulos.forEach((circulo) => {
      desenharBolinha(camadaOutras, circulo, { color: '#6b7280', fillColor: '#6b7280', fillOpacity: 0.12, weight: 1 })
        .bindTooltip(elemento('span', '', area.nome))
        .on('click', (evento) => {
          // Desenhando outra área, o toque vira bolinha nova; fora disso, abre esta área
          if (areaEditando) return
          L.DomEvent.stopPropagation(evento)
          editarArea(area)
        })
    })
  })

  desenharEdicao()

  areasEnquadrado = ajustarMapa(mapaAreas, areasEnquadrado)
}

function desenharEdicao() {
  if (!camadaEdicao) return
  camadaEdicao.clearLayers()
  camadaEscolhida = null
  if (!areaEditando) return

  areaEditando.circulos.forEach((circulo, indice) => {
    const escolhida = indice === bolinhaEscolhida
    const bolinha = desenharBolinha(camadaEdicao, circulo, {
      color: COR_DESENHO,
      fillColor: COR_DESENHO,
      weight: escolhida ? 4 : 2,
      fillOpacity: escolhida ? 0.35 : 0.25,
    }).on('click', (evento) => {
      L.DomEvent.stopPropagation(evento)
      escolherBolinha(indice)
    })
    if (escolhida) camadaEscolhida = bolinha

    // Ponto branco no centro: arrastar move a bolinha
    const alca = L.marker([Number(circulo.latitude), Number(circulo.longitude)], {
      icon: L.divIcon({ className: `alca${escolhida ? ' alca--escolhida' : ''}`, iconSize: escolhida ? [22, 22] : [18, 18] }),
      draggable: true,
      title: 'Arraste para mover a bolinha',
    }).addTo(camadaEdicao)

    alca.on('dragstart', () => escolherBolinha(indice, false))
    alca.on('drag', () => bolinha.setLatLng(alca.getLatLng()))
    alca.on('dragend', () => {
      const posicao = alca.getLatLng()
      circulo.latitude = Number(posicao.lat.toFixed(6))
      circulo.longitude = Number(posicao.lng.toFixed(6))
      desenharEdicao()
    })
  })

  atualizarControles()
}

function atualizarControles() {
  const circulo = areaEditando?.circulos[bolinhaEscolhida]
  $('#bloco-raio').hidden = !circulo
  if (circulo) {
    $('#area-raio').value = circulo.raio_m
    $('#area-raio-valor').textContent = formatarDistancia(circulo.raio_m)
  }

  const total = areaEditando?.circulos.length || 0
  $('#area-contagem').textContent = total
    ? `${total === 1 ? '1 bolinha' : `${total} bolinhas`} nesta área.`
    : 'Nenhuma bolinha ainda: toque no mapa para começar o desenho.'
}

function porBolinha(latlng) {
  if (!areaEditando) {
    statusAreas('Para desenhar, toque em "+ Nova área" ou escolha uma área na lista.')
    return
  }
  areaEditando.circulos.push({
    latitude: Number(latlng.lat.toFixed(6)),
    longitude: Number(latlng.lng.toFixed(6)),
    raio_m: RAIO_NOVO_M,
  })
  escolherBolinha(areaEditando.circulos.length - 1)
}

function escolherBolinha(indice, redesenhar = true) {
  bolinhaEscolhida = indice
  if (redesenhar) desenharEdicao()
  else atualizarControles()
}

function abrirEdicao(area) {
  // Cópia: nada muda no servidor até tocar em "Salvar área"
  areaEditando = {
    id: area?.id ?? null,
    nome: area?.nome ?? '',
    circulos: (area?.circulos ?? []).map((c) => ({ ...c, latitude: Number(c.latitude), longitude: Number(c.longitude) })),
  }
  bolinhaEscolhida = null

  formArea.hidden = false
  $('#area-form-titulo').textContent = area ? `Editar: ${area.nome}` : 'Nova área'
  $('#area-nome').value = areaEditando.nome
  $('#area-excluir').hidden = !area
  $('#area-excluir').textContent = 'Excluir área'
  $('#area-retorno').textContent = ''
  statusAreas(area ? `Editando ${area.nome}.` : 'Dê um nome e toque no mapa para pôr as bolinhas.')

  desenharListaAreas()
  desenharMapaAreas()
  $('#area-nome').focus()
}

function editarArea(area) {
  location.hash = '#areas'
  abrirEdicao(area)
  if (area.circulos.length && mapaAreas) enquadrarBolinhas(mapaAreas, area.circulos)
}

function fecharEdicao() {
  areaEditando = null
  bolinhaEscolhida = null
  formArea.hidden = true
  formArea.reset()
  statusAreas('Escolha uma área na lista ou crie uma nova.')
  desenharListaAreas()
  desenharMapaAreas()
}

$('#area-nova').addEventListener('click', () => abrirEdicao(null))
$('#area-cancelar').addEventListener('click', fecharEdicao)

$('#area-raio').addEventListener('input', (evento) => {
  const circulo = areaEditando?.circulos[bolinhaEscolhida]
  if (!circulo) return
  circulo.raio_m = Number(evento.target.value)
  // Só muda o tamanho da bolinha que já está no mapa: redesenhar tudo a cada passo pesa
  camadaEscolhida?.setRadius(circulo.raio_m)
  atualizarControles()
})

$('#bolinha-apagar').addEventListener('click', () => {
  if (bolinhaEscolhida === null) return
  areaEditando.circulos.splice(bolinhaEscolhida, 1)
  bolinhaEscolhida = null
  desenharEdicao()
})

formArea.addEventListener('submit', async (evento) => {
  evento.preventDefault()
  const novo = !areaEditando.id
  const corpo = {
    nome: $('#area-nome').value.trim(),
    circulos: areaEditando.circulos,
  }
  if (!corpo.circulos.length) {
    $('#area-retorno').textContent = 'Toque no mapa para pôr pelo menos uma bolinha antes de salvar.'
    return
  }
  $('#area-retorno').textContent = 'Salvando…'

  try {
    const resposta = await chamarApi(novo ? '/areas/' : `/areas/${areaEditando.id}/`, {
      metodo: novo ? 'POST' : 'PATCH',
      corpo,
    })
    if (resposta.status === 401) return irParaLogin()
    if (!resposta.ok) {
      $('#area-retorno').textContent = mensagemDeErro(await resposta.json().catch(() => null))
      return
    }

    const salva = await resposta.json()
    fecharEdicao()
    await carregarTudo()
    statusAreas(`Área ${salva.nome} salva. Ela já pode receber alertas na aba Alertas.`)
  } catch {
    $('#area-retorno').textContent = 'Sem conexão com o servidor. Tente de novo.'
  }
})

// Excluir pede um segundo toque. O primeiro só troca o texto do botão por 4 segundos.
// Devolve true no segundo toque, quando pode excluir de verdade
const timersDeExcluir = new Map()

function segundoToque(botao, rotulo) {
  if (botao.textContent !== rotulo) return true
  botao.textContent = 'Toque de novo para excluir'
  clearTimeout(timersDeExcluir.get(botao))
  timersDeExcluir.set(botao, setTimeout(() => (botao.textContent = rotulo), 4000))
  return false
}

$('#area-excluir').addEventListener('click', async (evento) => {
  const botao = evento.currentTarget
  if (!segundoToque(botao, 'Excluir área')) return

  try {
    const resposta = await chamarApi(`/areas/${areaEditando.id}/`, { metodo: 'DELETE' })
    if (resposta.status === 401) return irParaLogin()
    if (!resposta.ok) {
      const dados = await resposta.json().catch(() => null)
      $('#area-retorno').textContent = dados?.detail || 'Não foi possível excluir. Tente de novo.'
      botao.textContent = 'Excluir área'
      return
    }

    const nome = areaEditando.nome
    fecharEdicao()
    await carregarTudo()
    statusAreas(`Área ${nome} excluída.`)
  } catch {
    $('#area-retorno').textContent = 'Sem conexão com o servidor. Tente de novo.'
  }
})

// ---------- abrigos ----------

function contarAbrigosAbertos() {
  $('#total-abrigos').textContent = estado.abrigos.length
    ? estado.abrigos.filter((a) => ESTADOS_ABERTOS.includes(a.situacao)).length
    : '–'
  $('#total-abrigos-todos').textContent = estado.abrigos.length || '–'
}

function desenharTipos() {
  const seletor = $('#abrigo-tipo')
  const atual = seletor.value

  seletor.replaceChildren(
    ...estado.tipos.map((tipo) => {
      const opcao = elemento('option', '', `${tipo.icone} ${tipo.nome}`)
      opcao.value = tipo.id
      return opcao
    }),
  )
  if (atual) seletor.value = atual
}

const formAbrigo = $('#form-abrigo')
let editando = null // abrigo em edição, ou null quando é um abrigo novo
let ponto = null // { lat, lng } escolhido no mapa
let marcadorEdicao = null
let mapaAdmin = null
let camadaAbrigos = null

function mapaDoPainel() {
  if (typeof L === 'undefined') {
    mostrarStatus('O mapa não carregou. Confira a internet e recarregue a página.', true)
    return null
  }

  if (!mapaAdmin) {
    mapaAdmin = criarMapa($('#mapa-admin'), { zoom: 14 })
    camadaAbrigos = L.layerGroup().addTo(mapaAdmin)
    mapaAdmin.on('click', (evento) => escolherPonto(evento.latlng))
  }
  return mapaAdmin
}

function desenharMarcadores() {
  if (location.hash !== '#abrigos') return
  const mapa = mapaDoPainel()
  if (!mapa) return

  camadaAbrigos.clearLayers()
  const pontos = []

  estado.abrigos.forEach((abrigo) => {
    // O abrigo em edição é desenhado pelo marcador arrastável
    if (editando && editando.id === abrigo.id) return

    const posicao = [Number(abrigo.latitude), Number(abrigo.longitude)]
    pontos.push(posicao)

    const classes = abrigo.situacao === 'fechado' ? 'pin--fechado' : ''
    L.marker(posicao, { icon: iconePin(abrigo.tipo?.icone || '📍', classes), title: abrigo.nome })
      .on('click', () => editarAbrigo(abrigo))
      .addTo(camadaAbrigos)
  })

  setTimeout(() => {
    mapa.invalidateSize()
    if (!marcadorEdicao && pontos.length) mapa.fitBounds(pontos, { padding: [40, 40], maxZoom: 16 })
  }, 50)
}

function escolherPonto(latlng) {
  ponto = { lat: Number(latlng.lat.toFixed(6)), lng: Number(latlng.lng.toFixed(6)) }

  if (!marcadorEdicao) {
    marcadorEdicao = L.marker([ponto.lat, ponto.lng], {
      icon: iconePin('📍', 'pin--novo'),
      draggable: true,
      title: 'Posição do abrigo. Arraste para ajustar.',
    }).addTo(mapaAdmin)
    marcadorEdicao.on('dragend', () => escolherPonto(marcadorEdicao.getLatLng()))
  } else {
    marcadorEdicao.setLatLng([ponto.lat, ponto.lng])
  }

  $('#abrigo-posicao').textContent = `Posição: ${ponto.lat}, ${ponto.lng} · arraste o pino ou toque em outro ponto para ajustar.`

  if (formAbrigo.hidden) abrirFormulario()
}

function abrirFormulario() {
  formAbrigo.hidden = false
  $('#abrigo-form-titulo').textContent = editando ? `Editar: ${editando.nome}` : 'Novo abrigo'
  $('#abrigo-excluir').hidden = !editando
  $('#abrigo-excluir').textContent = 'Excluir'
  $('#abrigo-retorno').textContent = ''
  $('#abrigo-nome').focus()
}

function fecharFormulario() {
  formAbrigo.hidden = true
  formAbrigo.reset()
  $('#bloco-tipo-novo').hidden = true
  editando = null
  ponto = null
  if (marcadorEdicao) {
    marcadorEdicao.remove()
    marcadorEdicao = null
  }
  $('#abrigo-posicao').textContent = ''
  desenharMarcadores()
}

function editarAbrigo(abrigo) {
  fecharFormulario()
  editando = abrigo

  $('#abrigo-nome').value = abrigo.nome
  if (abrigo.tipo) $('#abrigo-tipo').value = abrigo.tipo.id
  $('#abrigo-situacao').value = abrigo.situacao
  $('#abrigo-referencia').value = abrigo.referencia || ''
  $('#abrigo-capacidade').value = abrigo.capacidade ?? ''

  desenharMarcadores()
  escolherPonto({ lat: Number(abrigo.latitude), lng: Number(abrigo.longitude) })
  mapaAdmin?.setView([Number(abrigo.latitude), Number(abrigo.longitude)], 17)
}

function mensagemDeErro(dados) {
  if (!dados || typeof dados !== 'object') return 'Não foi possível salvar.'
  const primeiro = Object.values(dados).flat()[0]
  return typeof primeiro === 'string' ? primeiro : 'Confira os dados e tente de novo.'
}

formAbrigo.addEventListener('submit', async (evento) => {
  evento.preventDefault()

  if (!ponto) {
    $('#abrigo-retorno').textContent = 'Toque no mapa para marcar onde fica o abrigo.'
    return
  }

  const capacidade = $('#abrigo-capacidade').value
  const corpo = {
    nome: $('#abrigo-nome').value.trim(),
    tipo: Number($('#abrigo-tipo').value),
    situacao: $('#abrigo-situacao').value,
    referencia: $('#abrigo-referencia').value.trim(),
    capacidade: capacidade === '' ? null : Number(capacidade),
    latitude: ponto.lat,
    longitude: ponto.lng,
  }

  $('#abrigo-retorno').textContent = 'Salvando…'

  try {
    const resposta = await chamarApi(editando ? `/abrigos/${editando.id}/` : '/abrigos/', {
      metodo: editando ? 'PATCH' : 'POST',
      corpo,
    })
    if (resposta.status === 401) return irParaLogin()

    if (!resposta.ok) {
      $('#abrigo-retorno').textContent = mensagemDeErro(await resposta.json().catch(() => null))
      return
    }

    fecharFormulario()
    await carregarTudo()
    mostrarStatus('Abrigo salvo. Ele já aparece no app dos moradores.')
  } catch {
    $('#abrigo-retorno').textContent = 'Sem conexão com o servidor. Tente de novo.'
  }
})

$('#abrigo-cancelar').addEventListener('click', fecharFormulario)

$('#abrigo-excluir').addEventListener('click', async (evento) => {
  if (!segundoToque(evento.currentTarget, 'Excluir')) return

  try {
    const resposta = await chamarApi(`/abrigos/${editando.id}/`, { metodo: 'DELETE' })
    if (resposta.status === 401) return irParaLogin()
    if (!resposta.ok) throw new Error('erro')

    fecharFormulario()
    await carregarTudo()
    mostrarStatus('Abrigo excluído.')
  } catch {
    $('#abrigo-retorno').textContent = 'Não foi possível excluir. Tente de novo.'
  }
})

// Tipo novo
$('#abrigo-tipo-novo').addEventListener('click', () => {
  $('#bloco-tipo-novo').hidden = false
  $('#tipo-novo-nome').focus()
})

$('#tipo-novo-criar').addEventListener('click', async () => {
  const nome = $('#tipo-novo-nome').value.trim()
  if (!nome) return $('#tipo-novo-nome').focus()

  try {
    const resposta = await chamarApi('/tipos-abrigo/', {
      metodo: 'POST',
      corpo: { nome, icone: $('#tipo-novo-icone').value.trim() || '📍' },
    })
    if (resposta.status === 401) return irParaLogin()

    if (!resposta.ok) {
      $('#abrigo-retorno').textContent = mensagemDeErro(await resposta.json().catch(() => null))
      return
    }

    const criado = await resposta.json()
    estado.tipos.push(criado)
    desenharTipos()
    $('#abrigo-tipo').value = criado.id
    $('#bloco-tipo-novo').hidden = true
    $('#tipo-novo-nome').value = ''
    $('#tipo-novo-icone').value = ''
    $('#abrigo-retorno').textContent = ''
  } catch {
    $('#abrigo-retorno').textContent = 'Sem conexão com o servidor. Tente de novo.'
  }
})

// Lista (também serve a quem não usa o mapa)
function desenharListaAbrigos() {
  const lista = $('#admin-abrigos-lista')
  lista.replaceChildren()

  if (!estado.abrigos.length) {
    lista.append(elemento('li', 'lista-abrigos__item', 'Nenhum abrigo cadastrado ainda. Toque no mapa para marcar o primeiro.'))
  }

  estado.abrigos.forEach((abrigo) => {
    const item = elemento('li', 'lista-abrigos__item')
    const texto = elemento('div')
    const tipo = abrigo.tipo ? `${abrigo.tipo.icone} ${abrigo.tipo.nome}` : 'Abrigo'

    texto.append(
      elemento('h3', 'lista-abrigos__nome', abrigo.nome),
      elemento('p', 'lista-abrigos__info', `${tipo} · ${SITUACOES[abrigo.situacao] || abrigo.situacao}`),
    )
    if (abrigo.referencia) texto.append(elemento('p', 'lista-abrigos__info', abrigo.referencia))

    const editar = elemento('button', 'botao botao--secundario', 'Editar')
    editar.type = 'button'
    editar.addEventListener('click', () => {
      location.hash = '#abrigos'
      editarAbrigo(abrigo)
    })

    item.append(texto, editar)
    lista.append(item)
  })
}

window.addEventListener('hashchange', desenharMapas)

// ---------- início ----------

preencherOrientacao()
carregarTudo()
