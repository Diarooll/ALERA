// App do morador: trava de login + dados reais do servidor (perfil, nível de risco e abrigos).
// Todo texto vindo do servidor entra na tela por textContent (ver elemento() em mapa.js).

const $ = (seletor) => document.querySelector(seletor)

// Botão Sair: o api.js avisa o servidor (sem travar se ele estiver fora) e só então vai para o login
async function encerrarSessao(evento) {
  evento?.preventDefault()
  await sairDaConta()
  location.replace('login.html')
}

// A sessão acabou de vez (o api.js já tentou renovar): limpa e volta para o login
function irParaLogin() {
  limparSessao()
  location.replace('login.html')
}

// Só volta para o login quando o servidor diz que a sessão não vale (401).
// Sem internet ou com o servidor fora do ar, a pessoa fica no app e vê o aviso de erro:
// numa emergência, perder a sessão por uma queda de rede é pior que esperar.
async function conferirLogin() {
  if (modoTesteAtivo()) return

  try {
    const resposta = await chamarApi('/me/')
    if (resposta.status === 401) irParaLogin()
  } catch {
    // sem resposta do servidor: carregarTudo() mostra o aviso
  }
}

$('#sair').addEventListener('click', encerrarSessao)

// pageshow também cobre o botão Voltar, que pode reabrir o app da memória sem rodar o <head>
window.addEventListener('pageshow', conferirLogin)

// ---------- movimento ----------

// Se o movimento.js não carregar, o app funciona igual, só sem animação
const mov =
  typeof Movimento !== 'undefined'
    ? Movimento
    : { observar() {}, aviso() {}, tremer() {}, vibrar() {}, reduzido: () => true }

// ---------- dados ----------

// Iguais ao README e à lista "O que fazer em cada nível" do app.html
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
    ordem: 'Chuva forte prevista em até 24 horas. Evite a rua e deixe documentos à mão.',
  },
  perigo: {
    nome: 'PERIGO',
    numero: 4,
    // A linha de baixo completa com o abrigo do morador: "Vá para o seu abrigo: ..."
    ordem: 'Risco agora. Saia de casa e vá para o abrigo.',
  },
}

const estado = {
  perfil: null,
  abrigos: [],
  erro: '',
  conferidoEm: null, // hora da última resposta boa do servidor
  pontos: 0,
  comemorar: false, // a missão do abrigo acabou de ser concluída: festeja quando a aba abrir
}

function semRede() {
  return navigator.onLine === false
}

function textoSemConexao() {
  return semRede()
    ? 'Sem internet agora. Assim que ela voltar, o app confere o nível de novo.'
    : 'O servidor não respondeu. Tente de novo em instantes.'
}

// Busca o perfil e os abrigos. Devolve false quando a sessão caiu (a pessoa já foi para o login).
// Sem rede o chamarApi lança erro: a pessoa continua no app com o último nível que chegou
async function buscarDados() {
  try {
    const [resPerfil, resAbrigos] = await Promise.all([chamarApi('/me/'), chamarApi('/abrigos/')])

    if (resPerfil.status === 401 || resAbrigos.status === 401) {
      irParaLogin()
      return false
    }
    if (!resPerfil.ok || !resAbrigos.ok) throw new Error('resposta com erro')

    estado.perfil = await resPerfil.json()
    estado.abrigos = await resAbrigos.json()
    estado.erro = ''
    estado.conferidoEm = new Date()
  } catch {
    estado.erro = textoSemConexao()
  }
  return true
}

// Modo teste (só neste computador): dados de exemplo para ver o visual sem servidor.
// O nível pode ser trocado em localStorage.modoTesteNivel (normal, atencao, alerta, perigo)
function dadosDeExemplo() {
  let nivel = 'alerta'
  try {
    nivel = localStorage.getItem('modoTesteNivel') || nivel
  } catch {
    // sem storage: fica o alerta
  }
  if (!NIVEIS[nivel]) nivel = 'alerta'

  const abrigo = (id, nome, tipo, situacao, latitude, longitude, distancia, minutos, referencia = '') => ({
    id, nome, tipo: { nome: tipo }, referencia, situacao, latitude, longitude, capacidade: 120,
    distancia_m: distancia, tempo_a_pe_min: minutos,
  })

  return {
    perfil: {
      email: 'morador@exemplo.com',
      papel: 'morador',
      telefone: '32999990000',
      cep: '36010002',
      logradouro: 'Rua Halfeld',
      numero: '414',
      complemento: '',
      bairro: 'Centro',
      cidade: 'Juiz de Fora',
      latitude: '-21.7608',
      longitude: '-43.3497',
      abrigo: null,
      alertas_ativos: true,
      area: { nome: 'Encosta do Centro', nivel, orientacao: '' },
      localizado: true,
    },
    abrigos: [
      abrigo(1, 'Escola Municipal do Centro', 'Escola', 'aberto', '-21.7625', '-43.3478', 270, 4, 'Entrada pelo portão lateral'),
      abrigo(2, 'Ginásio do Bairro', 'Ginásio', 'poucas', '-21.7655', '-43.3530', 620, 9),
      abrigo(3, 'Salão da Paróquia', 'Igreja', 'so-alerta', '-21.7570', '-43.3560', 770, 11),
      abrigo(4, 'Centro Comunitário', 'Centro comunitário', 'fechado', '-21.7680', '-43.3440', 990, 14),
    ],
  }
}

async function carregarTudo() {
  if (modoTesteAtivo()) {
    // Só na primeira vez: depois as mudanças feitas na tela ficam
    if (!estado.perfil) Object.assign(estado, dadosDeExemplo(), { conferidoEm: new Date() })
    return desenharTudo()
  }

  if (await buscarDados()) desenharTudo()
}

// A conferência de cada minuto redesenha só os textos do alerta e da rota.
// O formulário de Meus dados e os mapas ficam como estão: não apaga o que a pessoa
// está digitando nem tira o zoom que ela deu no mapa
async function atualizarAlerta() {
  if (await buscarDados()) {
    desenharAlerta({ anunciar: true })
    desenharRota()
  }
}

// Manda uma mudança do perfil. Devolve { ok, perfil } ou { ok: false, erros } (erros por campo).
// No modo teste a mudança fica só nesta tela. Sem rede, lança erro: quem chama trata
async function salvarPerfil(corpo) {
  if (modoTesteAtivo()) {
    Object.assign(estado.perfil, corpo)
    if ('latitude' in corpo) estado.perfil.localizado = corpo.latitude != null
    return { ok: true, perfil: estado.perfil }
  }

  const resposta = await chamarApi('/me/', { metodo: 'PATCH', corpo })
  if (resposta.status === 401) {
    irParaLogin()
    return { ok: false, saiu: true }
  }
  const dados = await resposta.json().catch(() => ({}))
  return resposta.ok ? { ok: true, perfil: dados } : { ok: false, erros: dados || {} }
}

// O primeiro texto de erro de um campo ({campo: ['texto']} ou {campo: 'texto'})
function primeiroErro(erros, campoNome) {
  const valor = erros?.[campoNome]
  if (Array.isArray(valor)) return valor.length ? String(valor[0]) : ''
  return valor ? String(valor) : ''
}

function abrigoSalvo() {
  return estado.abrigos.find((a) => a.id === estado.perfil?.abrigo) || null
}

// Para onde o morador vai: o abrigo que ele salvou ou, sem nenhum, o que recebe gente mais perto.
// Salvo e fechado não serve: vai para o aberto mais perto e "fechado" avisa isso na tela.
// A lista já vem do servidor do mais perto para o mais longe
function abrigoDestino() {
  const salvo = abrigoSalvo()
  if (salvo && salvo.situacao !== 'fechado') return { abrigo: salvo, salvo: true, fechado: null }

  const fechado = salvo || null
  const nivel = nivelDoMorador()
  const perto = posicaoCasa()
    ? estado.abrigos.find((a) => a.id !== fechado?.id && abrigoRecebe(a, nivel) && a.distancia_m != null)
    : null

  if (!perto && !fechado) return null
  return { abrigo: perto || null, salvo: false, fechado }
}

function nivelDoMorador() {
  const p = estado.perfil
  if (!p || !p.localizado) return null // sem o ponto da casa não dá para saber a área
  return p.area?.nivel || 'normal'
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

function horaCurta(data) {
  return data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

// Botão com estado de carregando: trava o clique duplo e diz o que está acontecendo
function carregando(botao, texto) {
  if (!botao) return () => {}
  const antes = botao.textContent
  botao.disabled = true
  botao.setAttribute('aria-busy', 'true')
  botao.classList.add('botao--carregando')
  botao.textContent = texto
  return () => {
    botao.disabled = false
    botao.removeAttribute('aria-busy')
    botao.classList.remove('botao--carregando')
    botao.textContent = antes
  }
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

    if (pontos.length > 1) item.mapa.fitBounds(pontos, { padding: [48, 48], maxZoom: 17 })
    else if (pontos.length === 1) item.mapa.setView(pontos[0], 16)
    else item.mapa.setView(CENTRO_MAPA, 13)
  }, 50)
}

// A linha da rota usa o azul do tema (no escuro, o azul claro)
function corDaLinha() {
  return getComputedStyle(document.documentElement).getPropertyValue('--app-azul').trim() || '#1E2A5A'
}

function pinCasa(item, posicao) {
  return L.marker(posicao, { icon: iconePin('Casa', 'pin--voce'), title: 'Sua casa', zIndexOffset: 500 }).addTo(
    item.camada,
  )
}

// O número do pino é a posição do abrigo na lista (do mais perto ao mais longe), igual à lista da janela
function pinAbrigo(item, abrigo, texto, classes) {
  const nome = elemento('span', '', abrigo.nome) // elemento, nunca texto: o Leaflet trataria como HTML
  return L.marker(posicaoAbrigo(abrigo), { icon: iconePin(texto, classes), title: abrigo.nome })
    .bindTooltip(nome, { direction: 'top', offset: [0, -40] })
    .addTo(item.camada)
}

function numeroDoAbrigo(abrigo) {
  return String(estado.abrigos.indexOf(abrigo) + 1)
}

function telaAtual() {
  return location.hash || '#alerta'
}

function desenharMapas() {
  const tela = telaAtual()
  const casa = posicaoCasa()
  const destino = abrigoDestino()?.abrigo || null

  if (tela === '#alerta' || tela === '#rota') {
    const item = mapaDe(tela === '#rota' ? 'rota' : 'alerta', tela === '#rota' ? '#mapa-rota' : '#mapa-alerta')
    if (!item) return

    const pontos = []
    if (casa) {
      pinCasa(item, casa)
      pontos.push(casa)
    }
    // Na tela de Alerta aparecem todos os abrigos que a Defesa Civil marcou.
    // Sem destino, o mapa enquadra todos; com destino, enquadra a casa e ele
    if (tela === '#alerta') {
      estado.abrigos
        .filter((abrigo) => abrigo.id !== destino?.id && abrigo.latitude != null)
        .forEach((abrigo) => {
          pinAbrigo(item, abrigo, numeroDoAbrigo(abrigo), abrigo.situacao === 'fechado' ? 'pin--fechado' : '')
          if (!destino) pontos.push(posicaoAbrigo(abrigo))
        })
    }
    if (destino) {
      pinAbrigo(item, destino, 'Abrigo', 'pin--salvo')
      pontos.push(posicaoAbrigo(destino))
    }
    if (casa && destino) {
      L.polyline([casa, posicaoAbrigo(destino)], { color: corDaLinha(), weight: 4, dashArray: '8 8' }).addTo(
        item.camada,
      )
    }
    enquadrar(item, pontos)
  }

  if (tela === '#detalhe-abrigo') desenharMapaAbrigos(casa)
  if (tela === '#cadastro') desenharMapaCasa(casa)
}

function desenharMapaAbrigos(casa) {
  const item = mapaDe('abrigos', '#mapa-abrigos')
  if (!item) return

  const pontos = []
  if (casa) {
    pinCasa(item, casa)
    pontos.push(casa)
  }

  estado.abrigos.forEach((abrigo) => {
    const classes =
      abrigo.situacao === 'fechado' ? 'pin--fechado' : abrigo.id === estado.perfil?.abrigo ? 'pin--salvo' : ''
    const marcador = L.marker(posicaoAbrigo(abrigo), {
      icon: iconePin(numeroDoAbrigo(abrigo), classes),
      title: abrigo.nome,
    }).addTo(item.camada)

    marcador.on('click', () => destacarAbrigo(abrigo.id))
    pontos.push(posicaoAbrigo(abrigo))
  })

  enquadrar(item, pontos)
}

function destacarAbrigo(id) {
  document.querySelectorAll('.abrigo-cartao').forEach((cartao) => {
    const ativo = Number(cartao.dataset.id) === id
    cartao.classList.toggle('abrigo-cartao--ativo', ativo)
    if (ativo) cartao.scrollIntoView({ block: 'nearest', behavior: mov.reduzido() ? 'auto' : 'smooth' })
  })
}

function desenharMapaCasa(casa) {
  const item = mapaDe('casa', '#mapa-casa')
  if (!item) return

  if (casa) pinCasa(item, casa)

  // Tocar no mapa marca a casa; o ponto vale mais que a busca pelo endereço
  item.mapa.off('click')
  item.mapa.on('click', (evento) => marcarCasa(item, evento.latlng))
  enquadrar(item, casa ? [casa] : [])
}

async function marcarCasa(item, ponto) {
  // O pino vai para o lugar tocado na hora; se não salvar, o mapa volta ao ponto antigo
  item.camada.clearLayers()
  pinCasa(item, [ponto.lat, ponto.lng])
  mostrarAviso('#casa-retorno', 'Salvando o ponto da casa…')

  try {
    const resultado = await salvarPerfil({
      latitude: Number(ponto.lat.toFixed(6)),
      longitude: Number(ponto.lng.toFixed(6)),
    })
    if (resultado.saiu) return
    if (!resultado.ok) {
      const texto =
        primeiroErro(resultado.erros, 'latitude') ||
        primeiroErro(resultado.erros, 'longitude') ||
        'Não foi possível salvar o ponto. Tente de novo.'
      mostrarAviso('#casa-retorno', texto, true)
      desenharMapaCasa(posicaoCasa())
      return
    }

    estado.perfil = resultado.perfil
    await carregarTudo() // a distância até os abrigos muda
    mostrarAviso('#casa-retorno', 'Ponto da casa salvo. A distância até os abrigos já usa ele.')
    mov.aviso('Ponto da casa salvo.', { tipo: 'ok' })
    mov.vibrar()
  } catch {
    mostrarAviso('#casa-retorno', `Não foi possível salvar o ponto. ${textoSemConexao()}`, true)
    desenharMapaCasa(posicaoCasa())
  }
}

// ---------- telas ----------

function desenharTudo() {
  desenharAlerta()
  desenharRota()
  desenharListaAbrigos()
  desenharMeusDados()
  desenharMissoes()
  desenharRanking()
  desenharMapas()
}

// ----- o campo do nível -----

// Troca a cor do campo. O texto muda na hora (data-nivel); o fundo novo desce como uma
// cortina por cima do antigo e só vira o fundo de verdade (data-fundo) quando ela termina
function pintarCampo(novo, { cortina = true } = {}) {
  const campoNivel = $('#campo-nivel')
  if (campoNivel.dataset.nivel === novo) return false

  campoNivel.dataset.nivel = novo
  campoNivel.querySelector('.campo-nivel__cortina')?.remove()

  if (!cortina || mov.reduzido()) {
    campoNivel.dataset.fundo = novo
    return true
  }

  const pano = elemento('span', 'campo-nivel__cortina')
  pano.dataset.fundo = novo
  pano.setAttribute('aria-hidden', 'true')
  campoNivel.prepend(pano)

  const assentar = () => {
    if (!pano.isConnected) return
    campoNivel.dataset.fundo = novo
    pano.remove()
  }
  pano.addEventListener('animationend', assentar, { once: true })
  setTimeout(assentar, 1400) // aba em segundo plano pode não avisar o fim da animação

  // A palavra do nível sobe de novo, junto com a cortina
  const palavra = $('#alerta-nivel')
  palavra.classList.remove('campo-nivel__palavra--sobe')
  void palavra.offsetWidth
  palavra.classList.add('campo-nivel__palavra--sobe')
  return true
}

function desenharAlerta({ anunciar = false } = {}) {
  const p = estado.perfil
  const nivel = nivelDoMorador()
  const info = nivel ? NIVEIS[nivel] : null
  const semDados = !p

  // A rua é a manchete do app: é o que a ALERA tem de diferente de uma previsão do tempo
  const rua = p?.logradouro ? [p.logradouro, p.numero].filter(Boolean).join(', ') : semDados ? 'Sua rua' : 'Endereço sem rua'
  $('#alerta-rua').textContent = rua

  if (!p) {
    $('#alerta-apoio').textContent = 'Sem dados da sua área agora'
  } else {
    const onde = !p.localizado ? 'casa não marcada no mapa' : p.area ? p.area.nome : 'fora das áreas de risco'
    $('#alerta-apoio').textContent = [p.bairro, onde].filter(Boolean).join(' · ')
  }

  const chave = info ? nivel : semDados ? 'erro' : 'sem-local'
  const antes = $('#campo-nivel').dataset.nivel
  $('#alerta-nivel').textContent = info ? info.nome : semDados ? 'SEM CONEXÃO' : 'SEM LOCAL'
  const mudou = pintarCampo(chave)

  // Nível novo na conferência de cada minuto: avisa e vibra (a primeira pintura, não)
  if (mudou && anunciar && info && NIVEIS[antes]) {
    const subiu = info.numero > NIVEIS[antes].numero
    mov.aviso(`O nível da sua rua mudou para ${info.nome}.`, {
      tipo: nivel === 'alerta' || nivel === 'perigo' ? 'erro' : 'info',
      tempo: 7000,
    })
    mov.vibrar(subiu ? [40, 80, 40, 80, 40] : 20)
  }

  const ordem = $('#alerta-ordem')
  if (info) {
    // A orientação escrita pela Defesa Civil vale mais que o texto padrão do nível
    ordem.textContent = (nivel !== 'normal' && p.area?.orientacao) || info.ordem
  } else if (p) {
    ordem.textContent = 'Marque o ponto da sua casa em Meus dados para receber os alertas da sua rua.'
  } else {
    ordem.textContent = 'Não conseguimos buscar o nível de risco da sua rua agora.'
  }

  // Mensagem personalizada: em qualquer nível acima do Normal, o alerta diz para onde ir
  const abrigo = $('#alerta-abrigo')
  const frase = nivel && nivel !== 'normal' ? fraseDoAbrigo(nivel, abrigoDestino()) : ''
  abrigo.textContent = frase
  abrigo.hidden = !frase

  const medidor = $('#alerta-medidor')
  medidor.hidden = !info
  medidor.setAttribute('aria-label', info ? `Nível ${info.numero} de 4` : 'Nível indisponível')
  medidor.querySelectorAll('.medidor__parte').forEach((parte, i) => {
    parte.classList.toggle('medidor__parte--cheia', info ? i < info.numero : false)
  })

  // Hora da conferência. Sem conexão, o nível que aparece é o último que chegou
  const hora = $('#alerta-hora')
  if (estado.erro && estado.conferidoEm) {
    hora.textContent = `${estado.erro} Nível conferido às ${horaCurta(estado.conferidoEm)}.`
  } else if (estado.erro) {
    hora.textContent = estado.erro
  } else if (estado.conferidoEm) {
    const teste = modoTesteAtivo() ? ' Modo teste: dados de exemplo.' : ''
    const qual = info ? `Nível ${info.numero} de 4` : 'Dados'
    hora.textContent = `${qual} conferido às ${horaCurta(estado.conferidoEm)}. O app confere de novo a cada minuto.${teste}`
  } else {
    hora.textContent = ''
  }
  $('#alerta-tentar').hidden = !estado.erro
  $('#alerta-marcar').hidden = !(p && !p.localizado)

  document.querySelectorAll('.niveis__item').forEach((item) => {
    const agora = item.dataset.nivel === nivel
    item.classList.toggle('niveis__item--agora', agora)
    if (agora) item.setAttribute('aria-current', 'true')
    else item.removeAttribute('aria-current')
  })

  desenharDestino(nivel)
}

$('#alerta-tentar').addEventListener('click', async (evento) => {
  const pronto = carregando(evento.currentTarget, 'Conferindo…')
  await carregarTudo()
  pronto()
  if (estado.erro) mov.aviso(estado.erro, { tipo: 'erro' })
})

// "Vá para o seu abrigo: Escola X, a 400 m (5 min a pé)."
function fraseDoAbrigo(nivel, destino) {
  if (!destino) return 'Você ainda não tem um abrigo. Toque em "Escolher meu abrigo" para saber para onde ir.'
  if (!destino.abrigo) {
    return `O seu abrigo, ${destino.fechado.nome}, está fechado e não achamos outro aberto perto. Ligue 199.`
  }

  const { abrigo, salvo, fechado } = destino
  const qual = salvo ? 'o seu abrigo' : 'o abrigo aberto mais perto'
  const distancia =
    abrigo.distancia_m != null ? `, a ${formatarDistancia(abrigo.distancia_m)} (${abrigo.tempo_a_pe_min} min a pé)` : ''
  const comeco = nivel === 'atencao' ? `Confira o caminho até ${qual}` : `Vá para ${qual}`
  const frase = `${comeco}: ${abrigo.nome}${distancia}.`
  return fechado ? `O seu abrigo está fechado agora. ${frase}` : frase
}

// Um número grande com a unidade pequena do lado ("270" "m")
function figura(numero, unidade) {
  const caixa = elemento('p', 'figura')
  caixa.append(elemento('span', 'figura__numero', numero), elemento('span', 'figura__unidade', unidade))
  return caixa
}

function desenharDestino(nivel) {
  const destino = abrigoDestino()
  const caixa = $('#destino-abrigo')
  const titulo = $('#destino-titulo')
  caixa.replaceChildren()

  // Em alerta ou perigo, o título vira ordem: "Vá para o seu abrigo"
  const urgente = nivel === 'alerta' || nivel === 'perigo'
  const abrigo = destino?.abrigo

  if (abrigo) {
    titulo.textContent = destino.salvo
      ? urgente ? 'Vá para o seu abrigo' : 'Seu abrigo'
      : urgente ? 'Vá para o abrigo aberto mais perto' : 'Abrigo aberto mais perto'

    caixa.append(elemento('p', 'destino__nome', abrigo.nome))
    if (abrigo.distancia_m != null) {
      const [valor, unidade] = formatarDistancia(abrigo.distancia_m).split(' ')
      const figuras = elemento('div', 'destino__figuras')
      figuras.append(figura(valor, unidade), figura(String(abrigo.tempo_a_pe_min), 'min a pé'))
      caixa.append(figuras)
    }
    const tipo = abrigo.tipo?.nome || 'Abrigo'
    caixa.append(elemento('p', 'destino__info', `${tipo} · ${SITUACOES[abrigo.situacao] || abrigo.situacao}`))
    if (abrigo.referencia) caixa.append(elemento('p', 'destino__info', abrigo.referencia))
  } else {
    titulo.textContent = 'Abrigo mais perto'
    if (!estado.perfil) {
      caixa.append(elemento('p', 'vazio', 'Sem conexão, não deu para buscar os abrigos. O 199 funciona mesmo assim.'))
    } else if (!posicaoCasa() && !destino) {
      const p = elemento('p', 'vazio', 'Não achamos sua casa no mapa, então não dá para medir a distância. ')
      const link = elemento('a', '', 'Marque o ponto em Meus dados.')
      link.href = '#cadastro'
      p.append(link)
      caixa.append(p)
    } else if (!estado.abrigos.length) {
      caixa.append(elemento('p', 'vazio', 'A Defesa Civil ainda não cadastrou abrigos. Em risco, ligue 199.'))
    } else if (!destino) {
      caixa.append(elemento('p', 'vazio', 'Nenhum abrigo aberto perto de você agora. Em risco, ligue 199.'))
    }
  }

  if (destino?.fechado) {
    caixa.append(
      elemento('p', 'destino__fechado', `Seu abrigo salvo, ${destino.fechado.nome}, está fechado agora.`),
    )
  }

  $('#ver-rota').hidden = !abrigo
  // Com abrigo salvo o botão continua na tela, para a pessoa poder trocar
  const escolher = $('#escolher-abrigo')
  escolher.textContent = destino?.salvo || destino?.fechado
    ? 'Trocar de abrigo'
    : estado.abrigos.length ? 'Escolher meu abrigo' : 'Ver abrigos'
  escolher.classList.toggle('botao--secundario', !!abrigo)
}

function desenharRota() {
  const destino = abrigoDestino()
  const abrigo = destino?.abrigo || null
  const caixa = $('#rota-destino')
  caixa.replaceChildren()

  if (abrigo) {
    caixa.append(elemento('h2', 'bloco-titulo', destino.salvo ? 'Seu abrigo' : 'Abrigo aberto mais perto'))
    caixa.append(elemento('p', 'destino__nome', abrigo.nome))
    caixa.append(elemento('p', 'destino__info', resumoAbrigo(abrigo)))
    if (abrigo.referencia) caixa.append(elemento('p', 'destino__info', abrigo.referencia))
    if (destino.fechado) {
      caixa.append(elemento('p', 'destino__fechado', `Seu abrigo salvo, ${destino.fechado.nome}, está fechado agora.`))
    }
  } else {
    caixa.append(elemento('h2', 'bloco-titulo', 'Sem abrigo para a rota'))
    caixa.append(elemento('p', 'vazio', 'Escolha seu abrigo na tela de Alerta para ver a rota.'))
  }

  const google = $('#rota-google')
  google.hidden = !abrigo
  if (abrigo) google.href = linkGoogleMaps(abrigo)

  const nivel = nivelDoMorador()
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

  if (estado.erro && !estado.abrigos.length) mostrarAviso('#abrigos-aviso', estado.erro, true)
  else if (!estado.abrigos.length) mostrarAviso('#abrigos-aviso', 'Nenhum abrigo cadastrado ainda. Assim que a Defesa Civil marcar um, ele aparece aqui.')
  else if (!posicaoCasa()) mostrarAviso('#abrigos-aviso', 'Sem o ponto da sua casa não dá para calcular a distância. Marque em Meus dados.')
  else mostrarAviso('#abrigos-aviso', 'Toque num pino ou na lista para escolher.')

  const nivel = nivelDoMorador()
  estado.abrigos.forEach((abrigo) => {
    const fechado = abrigo.situacao === 'fechado'
    const salvo = abrigo.id === estado.perfil?.abrigo

    const cartao = elemento('li', `abrigo-cartao${fechado ? ' abrigo-cartao--fechado' : ''}${salvo ? ' abrigo-cartao--salvo' : ''}`)
    cartao.dataset.id = abrigo.id

    const cabeca = elemento('div', 'abrigo-cartao__cabeca')
    cabeca.append(
      elemento('span', 'abrigo-cartao__numero', numeroDoAbrigo(abrigo)),
      elemento('h4', 'abrigo-cartao__nome', abrigo.nome),
    )
    cartao.append(cabeca, elemento('p', 'abrigo-cartao__info', `${abrigo.tipo?.nome || 'Abrigo'} · ${resumoAbrigo(abrigo)}`))
    if (abrigo.situacao === 'so-alerta') {
      const texto = abrigoRecebe(abrigo, nivel) ? 'Aberto agora, porque sua rua está em alerta.' : 'Abre quando o nível chegar a alerta.'
      cartao.append(elemento('p', 'abrigo-cartao__info', texto))
    }
    if (abrigo.referencia) cartao.append(elemento('p', 'abrigo-cartao__info', abrigo.referencia))

    const acoes = elemento('div', 'abrigo-cartao__acoes')

    const ver = elemento('button', 'botao botao--secundario pressionavel', 'Ver no mapa')
    ver.type = 'button'
    ver.addEventListener('click', () => {
      destacarAbrigo(abrigo.id)
      mapas.abrigos?.mapa.setView(posicaoAbrigo(abrigo), 17)
    })

    const salvar = elemento('button', 'botao pressionavel', salvo ? 'Abrigo salvo' : fechado ? 'Fechado' : 'Salvar este abrigo')
    salvar.type = 'button'
    salvar.disabled = fechado || salvo
    salvar.addEventListener('click', () => salvarAbrigo(abrigo.id, salvar))

    acoes.append(ver, salvar)
    cartao.append(acoes)
    lista.append(cartao)
  })

  mov.observar(lista.parentElement)
}

async function salvarAbrigo(id, botao) {
  const tinha = !!estado.perfil?.abrigo
  const pronto = carregando(botao, 'Salvando…')

  try {
    const resultado = await salvarPerfil({ abrigo: id })
    if (resultado.saiu) return
    if (!resultado.ok) {
      pronto()
      mov.aviso(primeiroErro(resultado.erros, 'abrigo') || 'Não foi possível salvar o abrigo. Tente de novo.', { tipo: 'erro' })
      return
    }

    estado.perfil = resultado.perfil
    // Primeiro abrigo salvo = missão concluída: a festa acontece quando a aba Missões abrir
    if (!tinha) estado.comemorar = true
    desenharTudo()
    mostrarAviso('#abrigos-aviso', 'Abrigo salvo. Ele aparece na tela de Alerta.')
    mov.aviso(tinha ? 'Abrigo trocado. Ele aparece na tela de Alerta.' : 'Abrigo salvo. Missão concluída: +10 pontos.', { tipo: 'ok' })
    mov.vibrar(tinha ? 12 : [12, 60, 24])
  } catch {
    pronto()
    mov.aviso(`Não foi possível salvar o abrigo. ${textoSemConexao()}`, { tipo: 'erro' })
  }
}

$('#abrigos-atualizar').addEventListener('click', async (evento) => {
  const pronto = carregando(evento.currentTarget, 'Atualizando…')
  await carregarTudo()
  pronto()
})

// ---------- Missões ----------

const formatoNumero = new Intl.NumberFormat('pt-BR')

// O total conta do valor antigo até o novo (sem movimento reduzido)
function contarAte(el, de, para, duracao = 900) {
  el.dataset.valor = String(para)
  if (mov.reduzido() || de === para) {
    el.textContent = formatoNumero.format(para)
    return
  }
  const inicio = performance.now()
  const quadro = (agora) => {
    const t = Math.min(1, (agora - inicio) / duracao)
    const suave = 1 - Math.pow(1 - t, 4)
    el.textContent = formatoNumero.format(Math.round(de + (para - de) * suave))
    if (t < 1) requestAnimationFrame(quadro)
  }
  requestAnimationFrame(quadro)
}

// "Salve seu abrigo" segue o que o morador fez. As outras ainda são exemplos fixos no HTML
function desenharMissoes() {
  const temAbrigo = !!estado.perfil?.abrigo
  const cartao = $('#missao-abrigo-cartao')
  cartao.querySelector('progress').value = temAbrigo ? 1 : 0
  cartao.querySelector('.progresso__legenda').textContent = temAbrigo ? 'Concluída' : 'Não iniciada'

  let concluidas = 0
  let pontos = 0
  let possiveis = 0
  const cartoes = document.querySelectorAll('#lista-missoes .missao')
  cartoes.forEach((missao) => {
    const progresso = missao.querySelector('progress')
    const feita = progresso.value >= progresso.max
    const valor = Number(missao.dataset.pontos) || 0
    possiveis += valor
    missao.toggleAttribute('data-concluida', feita)
    if (feita) {
      concluidas += 1
      pontos += valor
    }
  })
  estado.pontos = pontos

  const paraFazer = cartoes.length - concluidas
  $('#conta-fazer').textContent = String(paraFazer)
  $('#conta-concluidas').textContent = String(concluidas)

  // Esperando a festa, o total ainda mostra o valor antigo: quem sobe é a animação
  const total = $('#pontos-total')
  if (!estado.comemorar) {
    total.textContent = formatoNumero.format(pontos)
    total.dataset.valor = String(pontos)
    $('#pontos-barra').value = pontos
  }
  $('#pontos-barra').max = possiveis
  const faltam = possiveis - pontos
  $('#pontos-legenda').textContent = `${concluidas} de ${cartoes.length} missões concluídas · ${
    faltam ? `${formatoNumero.format(faltam)} pts ainda para ganhar` : 'todas feitas'
  }`

  // A aba aberta fica guardada em data-aba da lista ("fazer" ou "concluidas")
  const lista = $('#lista-missoes')
  const aba = lista.dataset.aba
  lista.setAttribute('aria-labelledby', `aba-${aba}`)
  $('#abas-missoes').dataset.aba = aba
  document.querySelectorAll('.aba-missao').forEach((botao) => {
    botao.setAttribute('aria-selected', String(botao.dataset.aba === aba))
  })

  const vazio = $('#missoes-vazio')
  const nenhuma = aba === 'fazer' ? paraFazer === 0 && !lista.querySelector('[data-comemorando]') : concluidas === 0
  vazio.hidden = !nenhuma
  vazio.textContent = aba === 'fazer'
    ? 'Você concluiu todas as missões. Elas estão na aba Concluídas.'
    : 'Nenhuma missão concluída ainda. Comece salvando o seu abrigo: leva um minuto.'
}

document.querySelectorAll('.aba-missao').forEach((botao) => {
  botao.addEventListener('click', () => {
    $('#lista-missoes').dataset.aba = botao.dataset.aba
    desenharMissoes()
  })
})

// O momento bom: o visto se desenha, os pontos pulam do cartão para o total e o total conta
function tocarComemoracao() {
  if (!estado.comemorar) return
  estado.comemorar = false

  const cartao = $('#missao-abrigo-cartao')
  const total = $('#pontos-total')
  const de = Number(total.dataset.valor) || 0
  const para = estado.pontos

  if (mov.reduzido()) {
    contarAte(total, de, para)
    $('#pontos-barra').value = para
    mov.aviso(`Missão concluída. Agora você tem ${formatoNumero.format(para)} pontos.`, { tipo: 'ok' })
    return desenharMissoes()
  }

  // Fica na aba Para fazer até a festa acabar, depois desliza para Concluídas
  cartao.setAttribute('data-comemorando', '')
  desenharMissoes()
  cartao.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  cartao.classList.add('missao--comemorando')

  setTimeout(() => {
    const origem = cartao.querySelector('.missao__valor').getBoundingClientRect()
    const destino = total.getBoundingClientRect()
    const ficha = elemento('span', 'ficha-pontos', cartao.querySelector('.missao__valor').textContent)
    ficha.setAttribute('aria-hidden', 'true')
    ficha.style.left = `${origem.left}px`
    ficha.style.top = `${origem.top}px`
    document.body.append(ficha)

    const dx = destino.left + destino.width / 2 - origem.left - origem.width / 2
    const dy = destino.top + destino.height / 2 - origem.top - origem.height / 2
    // Sobe num arco antes de cair no total
    const voo = ficha.animate(
      [
        { transform: 'translate(0, 0) scale(1)', opacity: 1 },
        { transform: `translate(${dx * 0.45}px, ${dy * 0.55 - 60}px) scale(1.25)`, opacity: 1, offset: 0.45 },
        { transform: `translate(${dx}px, ${dy}px) scale(.6)`, opacity: 0.2 },
      ],
      { duration: 760, easing: 'cubic-bezier(.65, 0, .35, 1)', fill: 'forwards' },
    )
    voo.onfinish = () => {
      ficha.remove()
      contarAte(total, de, para)
      $('#pontos-barra').value = para
      total.classList.remove('pontos__numero--pulo')
      void total.offsetWidth
      total.classList.add('pontos__numero--pulo')
      mov.vibrar(14)
    }
  }, 520)

  // Depois de tudo, a missão sai da lista Para fazer
  setTimeout(() => {
    cartao.classList.add('missao--saindo')
    const sair = () => {
      cartao.classList.remove('missao--comemorando', 'missao--saindo')
      cartao.removeAttribute('data-comemorando')
      desenharMissoes()
    }
    cartao.addEventListener('animationend', sair, { once: true })
    setTimeout(sair, 700)
  }, 2400)
}

// ---------- Ranking ----------

// Prévia com ruas de exemplo. A rua do morador soma os pontos dos vizinhos (exemplo) e os dele
const RUAS_EXEMPLO = [
  { rua: 'Rua Espírito Santo', pontos: 1240 },
  { rua: 'Rua Santo Antônio', pontos: 1015 },
  { rua: 'Rua Batista de Oliveira', pontos: 760 },
  { rua: 'Avenida Rio Branco', pontos: 610 },
  { rua: 'Rua Marechal Deodoro', pontos: 430 },
]
const PONTOS_VIZINHOS = 880

function desenharRanking() {
  const minhaRua = estado.perfil?.logradouro || 'Sua rua'
  const ruas = RUAS_EXEMPLO.filter((r) => r.rua.toLowerCase() !== minhaRua.toLowerCase())
    .concat({ rua: minhaRua, pontos: PONTOS_VIZINHOS + estado.pontos, sua: true })
    .sort((a, b) => b.pontos - a.pontos)
  const maior = ruas[0].pontos

  const lista = $('#ranking-lista')
  lista.replaceChildren()
  ruas.forEach((r, i) => {
    const item = elemento('li', `ranking__item${r.sua ? ' ranking__item--sua' : ''}`)
    if (r.sua) item.setAttribute('aria-current', 'true')

    const nome = elemento('span', 'ranking__nome', r.rua)
    if (r.sua) nome.append(elemento('span', 'ranking__sua', 'Sua rua'))

    // A barra é proporcional aos pontos: cresce até a fração da rua que lidera
    const barra = elemento('span', 'ranking__barra')
    const cheio = elemento('span', 'ranking__cheio')
    cheio.style.setProperty('--parte', (r.pontos / maior).toFixed(3))
    barra.setAttribute('aria-hidden', 'true')
    barra.append(cheio)

    item.append(
      elemento('span', 'ranking__posicao', String(i + 1)),
      nome,
      elemento('span', 'ranking__pontos', `${formatoNumero.format(r.pontos)} pts`),
      barra,
    )
    lista.append(item)
  })

  // O resumo da rua do morador: posição e quanto falta para passar a de cima
  const posicao = ruas.findIndex((r) => r.sua)
  const sua = ruas[posicao]
  $('#sua-rua-posicao').textContent = String(posicao + 1)
  $('#sua-rua-nome').textContent = `${minhaRua}, entre ${ruas.length} ruas`
  const texto = posicao === 0
    ? `${formatoNumero.format(sua.pontos)} pts. Sua rua lidera o ranking.`
    : `${formatoNumero.format(sua.pontos)} pts, ${formatoNumero.format(ruas[posicao - 1].pontos - sua.pontos)} atrás da ${ruas[posicao - 1].rua}. Seus pontos: ${formatoNumero.format(estado.pontos)}.`
  $('#sua-rua-texto').textContent = texto

  mov.observar(lista.parentElement)
}

// ---------- Meus dados ----------

const campo = {
  cep: $('#dados-cep'),
  rua: $('#dados-rua'),
  numero: $('#dados-numero'),
  semNumero: $('#dados-sem-numero'),
  complemento: $('#dados-complemento'),
  bairro: $('#dados-bairro'),
  cidade: $('#dados-cidade'),
}

// Nome do campo no servidor -> campo na tela (para mostrar o erro no lugar certo)
const CAMPOS_DO_SERVIDOR = {
  cep: campo.cep,
  logradouro: campo.rua,
  numero: campo.numero,
  complemento: campo.complemento,
  bairro: campo.bairro,
  cidade: campo.cidade,
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
  campo.complemento.value = p.complemento || ''
  campo.bairro.value = p.bairro || ''
  campo.cidade.value = p.cidade || ''
}

function formatarTelefoneApp(digitos) {
  const numero = digitos.slice(2)
  const corte = numero.length === 9 ? 5 : 4
  return `(${digitos.slice(0, 2)}) ${numero.slice(0, corte)}-${numero.slice(corte)}`
}

// Erro embaixo do campo: texto, aria-invalid e a borda vermelha (pelo CSS)
function erroNoCampo(entrada, texto) {
  const caixa = $(`#${entrada.id}-erro`)
  if (texto) entrada.setAttribute('aria-invalid', 'true')
  else entrada.removeAttribute('aria-invalid')
  if (caixa) {
    caixa.textContent = texto || ''
    caixa.hidden = !texto
  }
}

function limparErros() {
  Object.values(CAMPOS_DO_SERVIDOR).forEach((entrada) => erroNoCampo(entrada, ''))
}

// Confere antes de mandar. Devolve os campos com erro, na ordem do formulário
function conferirFormulario() {
  const erros = []
  if (!/^\d{5}-?\d{3}$/.test(campo.cep.value.trim())) erros.push([campo.cep, 'Digite o CEP com 8 números.'])
  if (!campo.rua.value.trim()) erros.push([campo.rua, 'Informe a rua.'])
  if (!campo.semNumero.checked && !campo.numero.value.trim()) {
    erros.push([campo.numero, 'Digite o número ou marque que a casa não tem número.'])
  }
  if (!campo.bairro.value.trim()) erros.push([campo.bairro, 'Informe o bairro.'])
  if (!campo.cidade.value.trim()) erros.push([campo.cidade, 'Informe a cidade.'])
  return erros
}

function mostrarErros(erros) {
  erros.forEach(([entrada, texto]) => erroNoCampo(entrada, texto))
  const [primeiro] = erros[0]
  primeiro.focus()
  mov.tremer(primeiro.closest('.campo'))
}

// Quem mexe no campo apaga o erro dele
Object.values(CAMPOS_DO_SERVIDOR).forEach((entrada) => {
  entrada.addEventListener('input', () => erroNoCampo(entrada, ''))
})

// Campo preenchido pelo CEP: entra com uma passada leve, um depois do outro
function preencherComCalma(entrada, ordem) {
  const caixa = entrada.closest('.campo')
  caixa.style.setProperty('--ordem', ordem)
  caixa.classList.remove('campo--preenchido')
  void caixa.offsetWidth
  caixa.classList.add('campo--preenchido')
}

campo.cep.addEventListener('input', async () => {
  campo.cep.value = formatarCep(campo.cep.value)
  const ajuda = $('#cep-ajuda')
  if (campo.cep.value.length !== 9) {
    ajuda.textContent = ''
    return
  }

  const cep = campo.cep.value
  ajuda.textContent = 'Buscando o endereço deste CEP…'
  const achado = await buscarCep(cep)
  if (campo.cep.value !== cep) return
  if (!achado) {
    ajuda.textContent = 'Não achamos este CEP. Preencha a rua, o bairro e a cidade.'
    return
  }

  let ordem = 0
  ;[
    [campo.rua, achado.logradouro],
    [campo.bairro, achado.bairro],
    [campo.cidade, achado.cidade],
  ].forEach(([entrada, valor]) => {
    if (!valor) return // CEP de cidade pequena vem sem rua: não apaga o que a pessoa escreveu
    entrada.value = valor
    erroNoCampo(entrada, '')
    preencherComCalma(entrada, ordem++)
  })
  ajuda.textContent = achado.logradouro ? 'Rua, bairro e cidade vieram do CEP. Falta o número.' : 'Cidade achada pelo CEP. Escreva a rua.'
  ;(achado.logradouro ? campo.numero : campo.rua).focus()
})

campo.semNumero.addEventListener('change', () => {
  campo.numero.disabled = campo.semNumero.checked
  if (campo.semNumero.checked) {
    campo.numero.value = ''
    erroNoCampo(campo.numero, '')
  }
})

$('#form-endereco').addEventListener('submit', async (evento) => {
  evento.preventDefault()
  limparErros()

  const errosAqui = conferirFormulario()
  if (errosAqui.length) return mostrarErros(errosAqui)

  const pronto = carregando($('#dados-salvar'), 'Salvando…')
  try {
    const resultado = await salvarPerfil({
      cep: campo.cep.value.replace(/\D/g, ''),
      logradouro: campo.rua.value.trim(),
      numero: campo.semNumero.checked ? 'S/N' : campo.numero.value.trim(),
      complemento: campo.complemento.value.trim(),
      bairro: campo.bairro.value.trim(),
      cidade: campo.cidade.value.trim(),
    })
    if (resultado.saiu) return

    if (!resultado.ok) {
      // O servidor manda {campo: ['texto']}: cada erro vai para baixo do seu campo
      const doServidor = Object.entries(CAMPOS_DO_SERVIDOR)
        .map(([nome, entrada]) => [entrada, primeiroErro(resultado.erros, nome)])
        .filter(([, texto]) => texto)
      if (doServidor.length) {
        mostrarErros(doServidor)
        mov.aviso('Confira o campo marcado.', { tipo: 'erro' })
      } else {
        const posicao = primeiroErro(resultado.erros, 'latitude') || primeiroErro(resultado.erros, 'longitude')
        if (posicao) mostrarAviso('#casa-retorno', posicao, true)
        const geral = primeiroErro(resultado.erros, 'non_field_errors') || primeiroErro(resultado.erros, 'detail')
        mov.aviso(posicao || geral || 'Não foi possível salvar. Confira os dados e tente de novo.', { tipo: 'erro' })
      }
      return
    }

    estado.perfil = resultado.perfil
    await carregarTudo() // bairro novo muda o nível; endereço novo muda as distâncias

    if (estado.perfil.localizado) {
      mov.aviso('Endereço salvo. Confira o ponto da casa no mapa ao lado.', { tipo: 'ok', tempo: 5000 })
      mov.vibrar()
    } else {
      mov.aviso('Endereço salvo, mas não achamos o ponto no mapa. Toque no mapa para marcar sua casa.', { tempo: 7000 })
    }
  } catch {
    mov.aviso(`Não foi possível salvar. ${textoSemConexao()}`, { tipo: 'erro', tempo: 6000 })
  } finally {
    pronto()
  }
})

// ---------- troca de abas ----------

// A ordem das abas no menu decide de que lado a tela nova entra
function lugarDaTela(hash) {
  if (hash.startsWith('#detalhe-')) return 1
  return { '#alerta': 0, '#rota': 0.5, '#missoes': 1, '#ranking': 2, '#cadastro': 3 }[hash] ?? 0
}

// A tela desliza e os blocos dela entram escalonados (app.css). A classe sai por tempo,
// e não no primeiro animationend: o fim da animação de um bloco filho também sobe até a tela
let fimEntrada = 0
function animarEntrada(hash, lado) {
  if (mov.reduzido()) return
  const tela = document.querySelector(hash)?.closest('.tela')
  if (!tela) return
  clearTimeout(fimEntrada)
  document.querySelectorAll('.tela--entra-frente, .tela--entra-tras').forEach((t) => {
    t.classList.remove('tela--entra-frente', 'tela--entra-tras')
  })
  void tela.offsetWidth
  tela.classList.add(`tela--entra-${lado}`)
  fimEntrada = setTimeout(() => tela.classList.remove(`tela--entra-${lado}`), 1100)
}

let telaAnterior = telaAtual()

window.addEventListener('hashchange', () => {
  const agora = telaAtual()
  // Janela de detalhe abre por cima: a tela de trás não se mexe
  const janela = agora.startsWith('#detalhe-') || telaAnterior.startsWith('#detalhe-')
  const de = lugarDaTela(telaAnterior)
  const para = lugarDaTela(agora)
  if (!janela && de !== para) animarEntrada(agora, para > de ? 'frente' : 'tras')
  telaAnterior = agora

  desenharMapas()
  if (agora === '#missoes') tocarComemoracao()
})

// ---------- início ----------

carregarTudo()

// Com o app aberto, confere o nível de novo a cada minuto: um alerta novo aparece sozinho
setInterval(() => {
  if (document.visibilityState === 'visible' && !modoTesteAtivo()) atualizarAlerta()
}, 60_000)

// A internet voltou: confere na hora, sem esperar o minuto
window.addEventListener('online', () => {
  if (!modoTesteAtivo()) atualizarAlerta()
})
