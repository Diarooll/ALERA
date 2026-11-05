// Prévia: nada é enviado nem salvo. Ao recarregar, a página volta aos dados de exemplo.
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
    orientacao: 'Chuva forte prevista em até 24 horas. Evite a rua e deixe documentos à mão.',
  },
  perigo: { nome: 'PERIGO', orientacao: 'Risco agora. Saia de casa e vá para o abrigo.' },
}
const ESTADOS_ABERTOS = ['aberto', 'poucas']

const form = document.querySelector('#form-alerta')
const campoRua = document.querySelector('#alerta-rua')
const campoMensagem = document.querySelector('#alerta-mensagem')
const confirmacao = document.querySelector('#confirmacao')
const linhasRuas = [...document.querySelectorAll('tr[data-rua]')]
const abrigos = [...document.querySelectorAll('[data-abrigo]')]

function nivelEscolhido() {
  return form.elements.nivel.value
}

function linhaDaRua() {
  return linhasRuas.find((linha) => linha.dataset.rua === campoRua.value)
}

function textoMoradores(linha) {
  return `${linha.dataset.moradores} moradores`
}

function mensagemAtual() {
  return campoMensagem.value.trim()
}

function atualizarPrevia() {
  const nivel = NIVEIS[nivelEscolhido()]
  const linha = linhaDaRua()

  document.querySelector('#previa-rua').textContent = campoRua.value
  document.querySelector('#previa-selo').className = `selo nivel--${nivelEscolhido()}`
  document.querySelector('#previa-nivel').textContent = nivel.nome
  document.querySelector('#previa-mensagem').textContent = mensagemAtual()
  document.querySelector('#previa-alcance').textContent =
    `Vai para ${textoMoradores(linha)}. Nível de agora nesta rua: ${NIVEIS[linha.dataset.nivel].nome}.`
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

function contarRuasEmRisco() {
  document.querySelector('#total-risco').textContent = linhasRuas.filter((linha) =>
    ['alerta', 'perigo'].includes(linha.dataset.nivel),
  ).length
}

function contarAbrigosAbertos() {
  document.querySelector('#total-abrigos').textContent = abrigos.filter((abrigo) =>
    ESTADOS_ABERTOS.includes(abrigo.value),
  ).length
}

function adicionarAoHistorico(nivelId, linha, mensagem) {
  const item = document.createElement('li')
  const etiqueta = document.createElement('span')
  const corpo = document.createElement('div')
  const rua = document.createElement('strong')
  const texto = document.createElement('p')
  const meta = document.createElement('p')

  item.className = 'historico__item'
  etiqueta.className = `etiqueta nivel--${nivelId}`
  etiqueta.textContent = NIVEIS[nivelId].nome
  rua.textContent = linha.dataset.rua
  texto.className = 'historico__texto'
  texto.textContent = mensagem
  meta.className = 'historico__meta'
  meta.textContent = `agora · ${textoMoradores(linha)} · simulação`

  corpo.append(rua, texto, meta)
  item.append(etiqueta, corpo)
  document.querySelector('#historico').prepend(item)
}

function registrarAlerta() {
  const nivelId = nivelEscolhido()
  const linha = linhaDaRua()
  const etiqueta = linha.querySelector('.etiqueta')

  linha.dataset.nivel = nivelId
  etiqueta.className = `etiqueta nivel--${nivelId}`
  etiqueta.textContent = NIVEIS[nivelId].nome

  adicionarAoHistorico(nivelId, linha, mensagemAtual())
  contarRuasEmRisco()
  atualizarPrevia()

  document.querySelector('#alerta-retorno').textContent =
    `Simulação: ${NIVEIS[nivelId].nome} registrado na ${linha.dataset.rua}. Nenhuma mensagem foi enviada.`
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

  const linha = linhaDaRua()

  document.querySelector('#confirmacao-titulo').textContent =
    `Enviar ${NIVEIS[nivelEscolhido()].nome} para ${textoMoradores(linha)} da ${linha.dataset.rua}?`
  document.querySelector('#confirmacao-mensagem').textContent = mensagemAtual()

  // Sem isto, fechar com Esc repetiria a resposta da confirmação anterior
  confirmacao.returnValue = ''
  confirmacao.showModal()
})

confirmacao.addEventListener('close', () => {
  if (confirmacao.returnValue === 'enviar') registrarAlerta()
})

abrigos.forEach((abrigo) => abrigo.addEventListener('change', contarAbrigosAbertos))

function encerrarSessao() {
  localStorage.removeItem('token')
  localStorage.removeItem('papel')
  localStorage.removeItem('modoTeste')
}

// O servidor decide quem é administrador. Se ele não confirmar, por qualquer motivo, a pessoa sai.
async function conferirAdministrador() {
  if (modoTesteAtivo() && localStorage.getItem('papel') === 'admin') return

  try {
    const resposta = await fetch(`${API_URL}/me/`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })

    if (resposta.ok && (await resposta.json()).papel === 'admin') return
  } catch {
    // sem resposta do servidor: trata como não confirmado
  }

  encerrarSessao()
  location.replace('login.html')
}

document.querySelector('#sair').addEventListener('click', encerrarSessao)

// pageshow também cobre o botão Voltar, que pode reabrir o painel da memória sem rodar o <head>
window.addEventListener('pageshow', conferirAdministrador)

preencherOrientacao()
atualizarPrevia()
contarAbrigosAbertos()
