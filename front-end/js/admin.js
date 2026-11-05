// Painel do administrador.
// Áreas, abrigos e tipos vêm do servidor. O envio de alerta continua simulado:
// nada é enviado e o nível mostrado aqui só muda nesta tela, até recarregar.
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
  perigo: { nome: 'PERIGO', orientacao: 'Risco agora. Saia de casa e vá para o abrigo.' },
}
const ESTADOS_ABERTOS = ['aberto', 'poucas']

const estado = { areas: [], abrigos: [], tipos: [] }

function encerrarSessao() {
  localStorage.removeItem('token')
  localStorage.removeItem('papel')
  localStorage.removeItem('modoTeste')
}

function irParaLogin() {
  encerrarSessao()
  location.replace('login.html')
}

// O servidor decide quem é administrador. Se ele não confirmar, por qualquer motivo, a pessoa sai.
async function conferirAdministrador() {
  if (modoTesteAtivo() && localStorage.getItem('papel') === 'admin') return

  try {
    const resposta = await chamarApi('/me/')

    if (resposta.ok && (await resposta.json()).papel === 'admin') return
  } catch {
    // sem resposta do servidor: trata como não confirmado
  }

  irParaLogin()
}

$('#sair').addEventListener('click', encerrarSessao)

// pageshow também cobre o botão Voltar, que pode reabrir o painel da memória sem rodar o <head>
window.addEventListener('pageshow', conferirAdministrador)

// ---------- carregar dados ----------

async function pegar(rota) {
  const resposta = await chamarApi(rota)
  if (resposta.status === 401 || resposta.status === 403) {
    irParaLogin()
    throw new Error('sessão')
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
    ;[estado.areas, estado.abrigos, estado.tipos] = await Promise.all([
      pegar('/areas/'),
      pegar('/abrigos/'),
      pegar('/tipos-abrigo/'),
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
  desenharTipos()
  desenharListaAbrigos()
  desenharMarcadores()
  contarAbrigosAbertos()
  atualizarPrevia()
}

// ---------- áreas de risco e alerta simulado ----------

const form = $('#form-alerta')
const campoArea = $('#alerta-rua')
const campoMensagem = $('#alerta-mensagem')
const confirmacao = $('#confirmacao')

function nivelEscolhido() {
  return form.elements.nivel.value
}

function areaEscolhida() {
  return estado.areas.find((a) => String(a.id) === campoArea.value)
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

  // O seletor do alerta guarda a área escolhida ao redesenhar
  const escolhida = campoArea.value
  campoArea.replaceChildren(
    ...estado.areas.map((area) => {
      const opcao = elemento('option', '', area.nome)
      opcao.value = area.id
      return opcao
    }),
  )
  if (escolhida) campoArea.value = escolhida

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
  const area = areaEscolhida()

  $('#previa-rua').textContent = area ? area.nome : 'Escolha uma área'
  $('#previa-selo').className = `selo nivel--${nivelEscolhido()}`
  $('#previa-nivel').textContent = nivel.nome
  $('#previa-mensagem').textContent = mensagemAtual()
  $('#previa-alcance').textContent = area
    ? `Vai para os moradores da área ${area.nome}. Nível de agora: ${NIVEIS[area.nivel].nome}.`
    : 'Cadastre uma área de risco no painel do Django para poder emitir alertas.'
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

function adicionarAoHistorico(nivelId, area, mensagem) {
  const item = elemento('li', 'historico__item')
  const corpo = elemento('div')

  corpo.append(
    elemento('strong', '', area.nome),
    elemento('p', 'historico__texto', mensagem),
    elemento('p', 'historico__meta', 'agora · simulação'),
  )
  item.append(elemento('span', `etiqueta nivel--${nivelId}`, NIVEIS[nivelId].nome), corpo)
  $('#historico').prepend(item)
}

function registrarAlerta() {
  const nivelId = nivelEscolhido()
  const area = areaEscolhida()

  area.nivel = nivelId // só nesta tela: o servidor não é avisado
  adicionarAoHistorico(nivelId, area, mensagemAtual())
  desenharAreas()
  atualizarPrevia()

  $('#alerta-retorno').textContent =
    `Simulação: ${NIVEIS[nivelId].nome} registrado na área ${area.nome}. Nenhuma mensagem foi enviada.`
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

  const area = areaEscolhida()
  if (!area) return

  $('#confirmacao-titulo').textContent =
    `Enviar ${NIVEIS[nivelEscolhido()].nome} para os moradores da área ${area.nome}?`
  $('#confirmacao-mensagem').textContent = mensagemAtual()

  // Sem isto, fechar com Esc repetiria a resposta da confirmação anterior
  confirmacao.returnValue = ''
  confirmacao.showModal()
})

confirmacao.addEventListener('close', () => {
  if (confirmacao.returnValue === 'enviar') registrarAlerta()
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
    if (resposta.status === 401 || resposta.status === 403) return irParaLogin()

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

// Excluir pede um segundo toque para confirmar
let timerExcluir = null

$('#abrigo-excluir').addEventListener('click', async (evento) => {
  const botao = evento.currentTarget

  if (botao.textContent === 'Excluir') {
    botao.textContent = 'Toque de novo para excluir'
    clearTimeout(timerExcluir)
    timerExcluir = setTimeout(() => (botao.textContent = 'Excluir'), 4000)
    return
  }

  try {
    const resposta = await chamarApi(`/abrigos/${editando.id}/`, { metodo: 'DELETE' })
    if (resposta.status === 401 || resposta.status === 403) return irParaLogin()
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
    if (resposta.status === 401 || resposta.status === 403) return irParaLogin()

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

window.addEventListener('hashchange', desenharMarcadores)

// ---------- início ----------

preencherOrientacao()
carregarTudo()
