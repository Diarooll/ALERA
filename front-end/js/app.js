// App do morador: trava de login + dados reais do servidor (perfil, nível de risco e abrigos).
// Todo texto vindo do servidor entra na tela por textContent (ver elemento() em mapa.js).

const $ = (seletor) => document.querySelector(seletor)

function encerrarSessao() {
  localStorage.removeItem('token')
  localStorage.removeItem('papel')
  localStorage.removeItem('modoTeste')
}

function irParaLogin() {
  encerrarSessao()
  location.replace('login.html')
}

// Se o servidor não confirmar o login, por qualquer motivo, a pessoa volta para o login.
async function conferirLogin() {
  if (modoTesteAtivo()) return

  try {
    const resposta = await chamarApi('/me/')
    if (resposta.ok) return
  } catch {
    // sem resposta do servidor: trata como não confirmado
  }

  irParaLogin()
}

$('#sair').addEventListener('click', encerrarSessao)

// pageshow também cobre o botão Voltar, que pode reabrir o app da memória sem rodar o <head>
window.addEventListener('pageshow', conferirLogin)

// ---------- dados ----------

const NIVEIS = {
  normal: {
    nome: 'NORMAL',
    numero: 1,
    ordem: 'Sem chuva forte prevista. Depois de muita chuva o solo ainda pode ceder: viu rachaduras, ligue 199.',
  },
  atencao: {
    nome: 'ATENÇÃO',
    numero: 2,
    ordem: 'Chuva prevista para hoje. Confira seu abrigo e tire o lixo da frente do bueiro.',
  },
  alerta: {
    nome: 'ALERTA',
    numero: 3,
    ordem: 'Chuva forte prevista em até 24 horas. Evite ruas alagadas e deixe documentos à mão.',
  },
  perigo: {
    nome: 'PERIGO',
    numero: 4,
    ordem: 'Risco agora. Saia de casa e vá para o abrigo.',
  },
}

const estado = { perfil: null, abrigos: [], erro: '' }

async function carregarTudo() {
  if (modoTesteAtivo()) {
    estado.erro = 'Modo teste: sem servidor, os dados reais não carregam.'
    return desenharTudo()
  }

  try {
    const [resPerfil, resAbrigos] = await Promise.all([chamarApi('/me/'), chamarApi('/abrigos/')])

    if (resPerfil.status === 401 || resAbrigos.status === 401) return irParaLogin()
    if (!resPerfil.ok || !resAbrigos.ok) throw new Error('resposta com erro')

    estado.perfil = await resPerfil.json()
    estado.abrigos = await resAbrigos.json()
    estado.erro = ''
  } catch {
    estado.erro = 'Não foi possível falar com o servidor. Tente de novo em instantes.'
  }

  desenharTudo()
}

function abrigoSalvo() {
  return estado.abrigos.find((a) => a.id === estado.perfil?.abrigo) || null
}

function posicaoCasa() {
  const p = estado.perfil
  return p && p.localizado ? [Number(p.latitude), Number(p.longitude)] : null
}

function posicaoAbrigo(abrigo) {
  return [Number(abrigo.latitude), Number(abrigo.longitude)]
}

function mostrarAviso(seletor, texto, erro = false) {
  const aviso = $(seletor)
  aviso.textContent = texto
  aviso.hidden = !texto
  aviso.classList.toggle('mapa-aviso--erro', erro)
}

// ---------- mapas ----------

const mapas = {}

function mapaDe(chave, seletor) {
  if (typeof L === 'undefined') return null // o Leaflet não carregou (sem internet)

  if (!mapas[chave]) {
    const mapa = criarMapa($(seletor), { zoom: 13 })
    mapas[chave] = { mapa, camada: L.layerGroup().addTo(mapa) }
  }

  mapas[chave].camada.clearLayers()
  return mapas[chave]
}

// O Leaflet precisa do tamanho real do mapa, que só existe depois de a tela aparecer
function enquadrar(item, pontos) {
  setTimeout(() => {
    item.mapa.invalidateSize()

    if (pontos.length > 1) item.mapa.fitBounds(pontos, { padding: [40, 40], maxZoom: 17 })
    else if (pontos.length === 1) item.mapa.setView(pontos[0], 16)
    else item.mapa.setView(CENTRO_MAPA, 13)
  }, 50)
}

function pinCasa(item, posicao) {
  L.marker(posicao, { icon: iconePin('🏠', 'pin--voce'), title: 'Sua casa' }).addTo(item.camada)
}

function telaAtual() {
  return location.hash || '#alerta'
}

function desenharMapas() {
  const tela = telaAtual()
  const casa = posicaoCasa()
  const salvo = abrigoSalvo()

  if (tela === '#alerta' || tela === '#rota') {
    const item = mapaDe(tela === '#rota' ? 'rota' : 'alerta', tela === '#rota' ? '#mapa-rota' : '#mapa-alerta')
    if (!item) return

    const pontos = []
    if (casa) {
      pinCasa(item, casa)
      pontos.push(casa)
    }
    if (salvo) {
      L.marker(posicaoAbrigo(salvo), { icon: iconePin(salvo.tipo?.icone || '📍', 'pin--salvo'), title: salvo.nome }).addTo(item.camada)
      pontos.push(posicaoAbrigo(salvo))
    }
    if (casa && salvo) {
      L.polyline([casa, posicaoAbrigo(salvo)], { color: '#1E2A5A', weight: 4, dashArray: '8 8' }).addTo(item.camada)
    }
    enquadrar(item, pontos)
  }

  if (tela === '#detalhe-abrigo') desenharMapaAbrigos(casa)
  if (tela === '#cadastro') desenharMapaCasa(casa)
}

let marcadoresAbrigos = {}

function desenharMapaAbrigos(casa) {
  const item = mapaDe('abrigos', '#mapa-abrigos')
  if (!item) return

  marcadoresAbrigos = {}
  const pontos = []

  if (casa) {
    pinCasa(item, casa)
    pontos.push(casa)
  }

  estado.abrigos.forEach((abrigo, indice) => {
    const classes = abrigo.situacao === 'fechado' ? 'pin--fechado' : abrigo.id === estado.perfil?.abrigo ? 'pin--salvo' : ''
    const marcador = L.marker(posicaoAbrigo(abrigo), {
      icon: iconePin(String(indice + 1), classes),
      title: abrigo.nome,
    }).addTo(item.camada)

    marcador.on('click', () => destacarAbrigo(abrigo.id))
    marcadoresAbrigos[abrigo.id] = marcador
    pontos.push(posicaoAbrigo(abrigo))
  })

  enquadrar(item, pontos)
}

function destacarAbrigo(id) {
  document.querySelectorAll('.abrigo-cartao').forEach((cartao) => {
    const ativo = Number(cartao.dataset.id) === id
    cartao.classList.toggle('abrigo-cartao--ativo', ativo)
    if (ativo) cartao.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

let pinDaCasa = null

function desenharMapaCasa(casa) {
  const item = mapaDe('casa', '#mapa-casa')
  if (!item) return

  pinDaCasa = null
  if (casa) {
    pinDaCasa = L.marker(casa, { icon: iconePin('🏠', 'pin--voce'), title: 'Sua casa' }).addTo(item.camada)
  }

  // Tocar no mapa marca a casa; o ponto vale mais que a busca pelo endereço
  item.mapa.off('click')
  item.mapa.on('click', (evento) => marcarCasa(item, evento.latlng))
  enquadrar(item, casa ? [casa] : [])
}

async function marcarCasa(item, ponto) {
  mostrarAviso('#casa-retorno', 'Salvando…')

  try {
    const resposta = await chamarApi('/me/', {
      metodo: 'PATCH',
      corpo: { latitude: Number(ponto.lat.toFixed(6)), longitude: Number(ponto.lng.toFixed(6)) },
    })
    if (resposta.status === 401) return irParaLogin()
    if (!resposta.ok) throw new Error('erro')

    estado.perfil = await resposta.json()
    await carregarTudo() // a distância até os abrigos muda
    mostrarAviso('#casa-retorno', 'Ponto da casa salvo.')
  } catch {
    mostrarAviso('#casa-retorno', 'Não foi possível salvar o ponto. Tente de novo.', true)
  }
}

// ---------- telas ----------

function desenharTudo() {
  desenharAlerta()
  desenharRota()
  desenharListaAbrigos()
  desenharMeusDados()
  desenharRanking()
  desenharMapas()
}

function desenharAlerta() {
  const p = estado.perfil

  $('#alerta-bairro').textContent = p?.bairro || 'Sua região'
  $('#alerta-apoio').textContent = p
    ? `${p.cidade}${p.area ? ` · ${p.area.nome}` : ' · região sem monitoramento cadastrado'}`
    : 'Sem dados'

  // Bairro sem área: aparece Normal, com um aviso
  const nivel = p ? p.area?.nivel || 'normal' : null
  const info = nivel ? NIVEIS[nivel] : null

  const selo = $('#alerta-selo')
  selo.className = nivel ? `selo nivel--${nivel}` : 'selo'
  $('#alerta-selo-texto').textContent = info ? info.nome : '…'
  $('#alerta-ordem').textContent = info ? info.ordem : 'Não conseguimos buscar o nível de risco agora.'

  const medidor = $('#alerta-medidor')
  medidor.setAttribute('aria-label', info ? `Nível ${info.numero} de 4` : 'Nível indisponível')
  medidor.querySelectorAll('.medidor__parte').forEach((parte, i) => {
    parte.classList.toggle('medidor__parte--cheia', info ? i < info.numero : false)
  })
  $('#alerta-medidor-legenda').textContent = info ? `Nível ${info.numero} de 4` : ''

  document.querySelectorAll('.niveis__item').forEach((item) => {
    const agora = item.dataset.nivel === nivel
    item.classList.toggle('niveis__item--agora', agora)
    if (agora) item.setAttribute('aria-current', 'true')
    else item.removeAttribute('aria-current')
  })

  if (estado.erro) mostrarAviso('#alerta-aviso', estado.erro, true)
  else if (p && !p.area) mostrarAviso('#alerta-aviso', 'Sua região ainda não tem monitoramento cadastrado. O nível mostrado é o Normal.')
  else mostrarAviso('#alerta-aviso', '')

  desenharDestino()
}

function desenharDestino() {
  const salvo = abrigoSalvo()
  const caixa = $('#destino-abrigo')
  caixa.replaceChildren()

  if (salvo) {
    caixa.append(
      elemento('p', 'destino__rotulo', 'Seu abrigo'),
      elemento('p', 'destino__nome', salvo.nome),
      elemento('p', 'destino__info', resumoAbrigo(salvo)),
    )
  } else if (estado.perfil && !posicaoCasa()) {
    const p = elemento('p', 'destino__info', 'Não achamos sua casa no mapa. ')
    const link = elemento('a', '', 'Marque o ponto em Meus dados.')
    link.href = '#cadastro'
    p.append(link)
    caixa.append(p)
  } else {
    caixa.append(elemento('p', 'destino__info', 'Você ainda não salvou um abrigo.'))
  }

  $('#ver-rota').hidden = !salvo
  $('#escolher-abrigo').hidden = !!salvo
  $('#escolher-abrigo').textContent = estado.abrigos.length ? 'Escolher meu abrigo' : 'Ver abrigos'
}

function desenharRota() {
  const salvo = abrigoSalvo()
  const destino = $('#rota-destino')
  destino.replaceChildren()

  if (salvo) {
    destino.append(
      elemento('h2', 'rota__nome', salvo.nome),
      elemento('p', 'destino__info', resumoAbrigo(salvo)),
    )
    if (salvo.referencia) destino.append(elemento('p', 'destino__info', salvo.referencia))
  } else {
    destino.append(elemento('p', 'destino__info', 'Salve um abrigo em Missões para ver a rota.'))
  }

  const google = $('#rota-google')
  google.hidden = !salvo
  if (salvo) google.href = linkGoogleMaps(salvo)

  const nivel = estado.perfil?.area?.nivel
  const evitar = $('#rota-evitar')
  const perigoso = nivel === 'alerta' || nivel === 'perigo'
  evitar.hidden = !perigoso
  evitar.className = perigoso ? `rota__evitar nivel--${nivel}` : 'rota__evitar'
  if (perigoso) {
    $('#rota-evitar-texto').textContent = `${NIVEIS[nivel].nome} · Evite ruas alagadas e encostas no caminho.`
  }
}

function desenharListaAbrigos() {
  const lista = $('#abrigos-lista')
  lista.replaceChildren()

  if (estado.erro) mostrarAviso('#abrigos-aviso', estado.erro, true)
  else if (!estado.abrigos.length) mostrarAviso('#abrigos-aviso', 'Nenhum abrigo cadastrado ainda. Assim que a Defesa Civil marcar um, ele aparece aqui.')
  else if (!posicaoCasa()) mostrarAviso('#abrigos-aviso', 'Sem o ponto da sua casa não dá para calcular a distância. Marque em Meus dados.')
  else mostrarAviso('#abrigos-aviso', 'Toque num pino ou na lista para escolher.')

  estado.abrigos.forEach((abrigo, indice) => {
    const fechado = abrigo.situacao === 'fechado'
    const salvo = abrigo.id === estado.perfil?.abrigo

    const cartao = elemento('li', `abrigo-cartao${fechado ? ' abrigo-cartao--fechado' : ''}`)
    cartao.dataset.id = abrigo.id

    const tipo = abrigo.tipo ? `${abrigo.tipo.icone} ${abrigo.tipo.nome}` : 'Abrigo'
    cartao.append(
      elemento('h4', 'abrigo-cartao__nome', `${indice + 1}. ${abrigo.nome}`),
      elemento('p', 'abrigo-cartao__info', `${tipo} · ${resumoAbrigo(abrigo)}`),
    )
    if (abrigo.referencia) cartao.append(elemento('p', 'abrigo-cartao__info', abrigo.referencia))

    const acoes = elemento('div', 'abrigo-cartao__acoes')

    const ver = elemento('button', 'botao botao--secundario', 'Ver no mapa')
    ver.type = 'button'
    ver.addEventListener('click', () => {
      destacarAbrigo(abrigo.id)
      mapas.abrigos?.mapa.setView(posicaoAbrigo(abrigo), 17)
    })

    const salvar = elemento('button', 'botao', salvo ? 'Abrigo salvo ✓' : fechado ? 'Fechado' : 'Salvar este abrigo')
    salvar.type = 'button'
    salvar.disabled = fechado || salvo
    salvar.addEventListener('click', () => salvarAbrigo(abrigo.id))

    acoes.append(ver, salvar)
    cartao.append(acoes)
    lista.append(cartao)
  })
}

async function salvarAbrigo(id) {
  mostrarAviso('#abrigos-aviso', 'Salvando…')

  try {
    const resposta = await chamarApi('/me/', { metodo: 'PATCH', corpo: { abrigo: id } })
    if (resposta.status === 401) return irParaLogin()
    if (!resposta.ok) throw new Error('erro')

    estado.perfil = await resposta.json()
    desenharTudo()
    mostrarAviso('#abrigos-aviso', 'Abrigo salvo! Ele aparece na tela de Alerta.')
  } catch {
    mostrarAviso('#abrigos-aviso', 'Não foi possível salvar o abrigo. Tente de novo.', true)
  }
}

$('#abrigos-atualizar').addEventListener('click', carregarTudo)

function desenharRanking() {
  $('#ranking-bairro').textContent = estado.perfil?.bairro || 'Seu bairro'
}

// ---------- Meus dados ----------

const campo = {
  cep: $('#dados-cep'),
  rua: $('#dados-rua'),
  numero: $('#dados-numero'),
  semNumero: $('#dados-sem-numero'),
  bairro: $('#dados-bairro'),
  cidade: $('#dados-cidade'),
}

function desenharMeusDados() {
  const p = estado.perfil
  if (!p) return

  const telefone = p.telefone ? formatarTelefoneApp(p.telefone) : ''
  $('#dados-contato').textContent = `${p.email}${telefone ? ` · ${telefone}` : ''}`

  // Não apaga o que a pessoa está digitando
  if (document.activeElement && document.activeElement.closest('#form-endereco')) return

  campo.cep.value = formatarCep(p.cep || '')
  campo.rua.value = p.logradouro || ''
  campo.semNumero.checked = p.numero === 'S/N'
  campo.numero.value = p.numero === 'S/N' ? '' : p.numero || ''
  campo.numero.disabled = campo.semNumero.checked
  campo.bairro.value = p.bairro || ''
  campo.cidade.value = p.cidade || ''
}

function formatarTelefoneApp(digitos) {
  const numero = digitos.slice(2)
  const corte = numero.length === 9 ? 5 : 4
  return `(${digitos.slice(0, 2)}) ${numero.slice(0, corte)}-${numero.slice(corte)}`
}

campo.cep.addEventListener('input', async () => {
  campo.cep.value = formatarCep(campo.cep.value)
  if (campo.cep.value.length !== 9) return

  const cep = campo.cep.value
  const achado = await buscarCep(cep)
  if (campo.cep.value !== cep || !achado) return

  campo.rua.value = achado.logradouro
  campo.bairro.value = achado.bairro
  campo.cidade.value = achado.cidade
  campo.numero.focus()
})

campo.semNumero.addEventListener('change', () => {
  campo.numero.disabled = campo.semNumero.checked
  if (campo.semNumero.checked) campo.numero.value = ''
})

$('#form-endereco').addEventListener('submit', async (evento) => {
  evento.preventDefault()

  if (!campo.semNumero.checked && !campo.numero.value.trim()) {
    mostrarAviso('#dados-retorno', 'Digite o número ou marque que a casa não tem número.', true)
    campo.numero.focus()
    return
  }

  mostrarAviso('#dados-retorno', 'Salvando…')

  try {
    const resposta = await chamarApi('/me/', {
      metodo: 'PATCH',
      corpo: {
        cep: campo.cep.value.replace(/\D/g, ''),
        logradouro: campo.rua.value.trim(),
        numero: campo.semNumero.checked ? 'S/N' : campo.numero.value.trim(),
        bairro: campo.bairro.value.trim(),
        cidade: campo.cidade.value.trim(),
      },
    })
    if (resposta.status === 401) return irParaLogin()
    if (!resposta.ok) throw new Error('erro')

    estado.perfil = await resposta.json()
    await carregarTudo() // bairro novo muda o nível; endereço novo muda as distâncias

    mostrarAviso(
      '#dados-retorno',
      estado.perfil.localizado
        ? 'Endereço salvo e casa localizada no mapa.'
        : 'Endereço salvo, mas não achamos o ponto no mapa. Toque no mapa abaixo para marcar sua casa.',
    )
  } catch {
    mostrarAviso('#dados-retorno', 'Não foi possível salvar. Confira os dados e tente de novo.', true)
  }
})

// ---------- início ----------

window.addEventListener('hashchange', desenharMapas)
carregarTudo()
