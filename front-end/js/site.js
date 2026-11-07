// ALERA · site.js
// Scripts do site (index.html). O site funciona sem eles: as cores dos níveis e a
// mensagem trocam só com CSS. Aqui ficam três coisas a mais:
//   1. o nome da rua digitado entra na mensagem (sempre por textContent)
//   2. a chuva desenhada no <canvas>, mais forte a cada nível, na cor do nível
//   3. os modelos 3D dos gadgets (abrir, girar arrastando, separar as peças)

;(() => {
  // ---------- 1. Nome da rua na mensagem ----------

  const campoRua = document.querySelector('#rua')
  const nomesRua = document.querySelectorAll('.rua-nome')
  const formulario = document.querySelector('.teste')
  const RUA_PADRAO = 'Rua Exemplo'

  function atualizarRua() {
    // Limpa espaços repetidos e corta em 60 letras. textContent: o texto nunca vira HTML.
    const nome = campoRua.value.replace(/\s+/g, ' ').trim().slice(0, 60) || RUA_PADRAO
    nomesRua.forEach((el) => (el.textContent = nome))
  }

  if (campoRua) {
    campoRua.addEventListener('input', atualizarRua)
    atualizarRua() // o navegador pode ter guardado o que a pessoa digitou antes
  }
  // Enter no campo não envia nada: é só demonstração
  if (formulario) formulario.addEventListener('submit', (evento) => evento.preventDefault())

  // ---------- 2. Chuva no canvas ----------
  // Roda sempre, mesmo com "menos movimento" no sistema (decisão do dono do projeto).

  const secao = document.querySelector('.sua-rua')
  const tela = document.querySelector('.chuva')
  const radios = document.querySelectorAll('.nivel-radio')

  // Quanto chove em cada nível (0 a 1)
  const FORCA = { normal: 0.12, atencao: 0.38, alerta: 0.68, perigo: 1 }
  const MAX_GOTAS = 200

  if (secao && tela && tela.getContext) {
    const ctx = tela.getContext('2d')
    const gotas = []
    let largura = 0
    let altura = 0
    let visivel = false
    let quadro = 0
    const marcado = document.querySelector('.nivel-radio:checked')
    let forcaAlvo = FORCA[marcado ? marcado.value : 'alerta'] ?? FORCA.alerta
    let forcaAtual = forcaAlvo

    function novaGota(espalhar) {
      return {
        x: Math.random() * (largura + 200) - 100,
        y: espalhar ? Math.random() * altura : -40 - Math.random() * altura * 0.3,
        tam: 12 + Math.random() * 20,
        vel: 0.7 + Math.random() * 0.6,
      }
    }

    function medir() {
      // Até 2x de densidade de pixels: mais que isso gasta bateria sem mudar o que se vê
      const dpr = Math.min(devicePixelRatio || 1, 2)
      largura = secao.clientWidth
      altura = secao.clientHeight
      tela.width = Math.round(largura * dpr)
      tela.height = Math.round(altura * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      gotas.length = 0
      for (let i = 0; i < MAX_GOTAS; i++) gotas.push(novaGota(true))
      if (!rodando()) desenhar(0)
    }

    function desenhar(passo) {
      ctx.clearRect(0, 0, largura, altura)
      // A chuva usa a cor do nível (--nivel-cor muda suave pelo CSS) sobre o azul-noite
      ctx.strokeStyle = getComputedStyle(secao).getPropertyValue('--nivel-cor').trim() || '#F07A1A'
      ctx.globalAlpha = 0.3 + forcaAtual * 0.25
      ctx.lineWidth = 1.2 + forcaAtual
      ctx.lineCap = 'round'
      const quantas = Math.round(MAX_GOTAS * forcaAtual)
      const vento = 0.12 + forcaAtual * 0.18 // mais vento, gota mais inclinada
      const rapidez = 9 + forcaAtual * 14
      ctx.beginPath()
      for (let i = 0; i < quantas; i++) {
        const g = gotas[i]
        g.y += g.vel * rapidez * passo
        g.x += g.vel * rapidez * vento * passo
        if (g.y > altura + 40) Object.assign(g, novaGota(false))
        const tam = g.tam * (0.7 + forcaAtual * 0.6)
        ctx.moveTo(g.x, g.y)
        ctx.lineTo(g.x - tam * vento, g.y - tam)
      }
      ctx.stroke()
    }

    const rodando = () => visivel && !document.hidden

    let ultimo = 0
    function animar(agora) {
      quadro = 0
      if (!rodando()) return
      // passo = quantos "quadros de 60 Hz" passaram; segura saltos quando a aba volta
      const passo = ultimo ? Math.min((agora - ultimo) / 16.7, 3) : 1
      ultimo = agora
      forcaAtual += (forcaAlvo - forcaAtual) * 0.05 // a chuva engrossa aos poucos
      desenhar(passo)
      quadro = requestAnimationFrame(animar)
    }

    function ligar() {
      if (quadro || !rodando()) return
      ultimo = 0
      quadro = requestAnimationFrame(animar)
    }

    // Só chove quando a demonstração está na tela e a aba está aberta
    if ('IntersectionObserver' in window) {
      new IntersectionObserver((entradas) => {
        visivel = entradas[0].isIntersecting
        ligar()
      }).observe(secao)
    } else {
      visivel = true
    }
    document.addEventListener('visibilitychange', ligar)

    if ('ResizeObserver' in window) new ResizeObserver(medir).observe(secao)
    else addEventListener('resize', medir)

    medir()
    ligar()

    radios.forEach((radio) =>
      radio.addEventListener('change', () => {
        forcaAlvo = FORCA[radio.value] ?? FORCA.alerta
        if (window.Movimento) Movimento.vibrar(radio.value === 'perigo' ? [20, 40, 20] : 10)
      }),
    )
  }

  // ---------- 3. Modelos 3D dos gadgets ----------
  // O modelo é todo em CSS 3D (index.html + site.css). Aqui só:
  //   - abrir e fechar o <dialog> (Esc fecha sozinho, é do próprio <dialog>)
  //   - girar: arrastar com mouse ou dedo (pointer events) ou setas do teclado
  //   - girar devagar sozinho quando ninguém mexe há um tempo
  //   - "Separar peças": liga a classe .separado (a animação é do CSS)
  // A rotação vai para --rx e --ry da .cena (style.setProperty: valor nosso, nunca dado de fora).

  const RX_INICIO = -18
  const RY_INICIO = -32
  const ESPERA_GIRO = 1800 // ms parado antes do giro automático voltar

  function prepararModelo(dialogo) {
    const palco = dialogo.querySelector('.palco')
    const cena = dialogo.querySelector('.cena')
    const botaoSeparar = dialogo.querySelector('[data-separar]')
    const botaoInicio = dialogo.querySelector('[data-girar-inicio]')
    let rx = RX_INICIO
    let ry = RY_INICIO
    let arrastando = null // { id, x, y }
    let ultimoToque = 0
    let voltando = false
    let quadro = 0
    let ultimo = 0

    const limitar = (v, min, max) => Math.min(max, Math.max(min, v))

    function aplicar() {
      cena.style.setProperty('--rx', rx.toFixed(2) + 'deg')
      cena.style.setProperty('--ry', ry.toFixed(2) + 'deg')
    }

    function passoAnimacao(agora) {
      quadro = 0
      if (!dialogo.open) return
      const passo = ultimo ? Math.min((agora - ultimo) / 16.7, 3) : 1
      ultimo = agora
      if (voltando) {
        rx += (RX_INICIO - rx) * 0.12 * passo
        ry += (RY_INICIO - ry) * 0.12 * passo
        if (Math.abs(rx - RX_INICIO) < 0.1 && Math.abs(ry - RY_INICIO) < 0.1) {
          rx = RX_INICIO
          ry = RY_INICIO
          voltando = false
          ultimoToque = agora
        }
      } else if (!arrastando && agora - ultimoToque > ESPERA_GIRO) {
        ry += 0.18 * passo // giro automático leve
      }
      aplicar()
      quadro = requestAnimationFrame(passoAnimacao)
    }

    function abrir() {
      if (!dialogo.open) dialogo.showModal()
      ultimo = 0
      ultimoToque = performance.now()
      aplicar()
      if (!quadro) quadro = requestAnimationFrame(passoAnimacao)
    }

    palco.addEventListener('pointerdown', (evento) => {
      if (evento.button !== 0) return
      arrastando = { id: evento.pointerId, x: evento.clientX, y: evento.clientY }
      voltando = false
      palco.setPointerCapture(evento.pointerId)
    })
    palco.addEventListener('pointermove', (evento) => {
      if (!arrastando || evento.pointerId !== arrastando.id) return
      ry += (evento.clientX - arrastando.x) * 0.45
      rx = limitar(rx - (evento.clientY - arrastando.y) * 0.35, -75, 15)
      arrastando.x = evento.clientX
      arrastando.y = evento.clientY
    })
    function soltar() {
      arrastando = null
      ultimoToque = performance.now()
    }
    palco.addEventListener('pointerup', soltar)
    palco.addEventListener('pointercancel', soltar)

    // Teclado: setas giram 10 graus
    palco.addEventListener('keydown', (evento) => {
      const giros = { ArrowLeft: [0, -10], ArrowRight: [0, 10], ArrowUp: [5, 0], ArrowDown: [-5, 0] }
      const giro = giros[evento.key]
      if (!giro) return
      evento.preventDefault()
      voltando = false
      rx = limitar(rx + giro[0], -75, 15)
      ry += giro[1]
      ultimoToque = performance.now()
    })

    botaoSeparar.addEventListener('click', () => {
      const separado = dialogo.classList.toggle('separado')
      botaoSeparar.setAttribute('aria-pressed', String(separado))
      botaoSeparar.textContent = separado ? 'Juntar peças' : 'Separar peças'
      ultimoToque = performance.now()
    })

    botaoInicio.addEventListener('click', () => {
      // Traz o giro para perto do início antes de voltar, para não dar várias voltas
      ry = ((((ry - RY_INICIO) % 360) + 540) % 360) - 180 + RY_INICIO
      voltando = true
    })

    dialogo.querySelectorAll('[data-fechar-modelo]').forEach((botao) =>
      botao.addEventListener('click', () => dialogo.close()),
    )
    // Clique fora do cartão (no fundo escurecido) também fecha
    dialogo.addEventListener('click', (evento) => {
      if (evento.target === dialogo) dialogo.close()
    })
    dialogo.addEventListener('close', () => {
      cancelAnimationFrame(quadro)
      quadro = 0
      arrastando = null
    })

    return abrir
  }

  document.querySelectorAll('[data-abrir-modelo]').forEach((botao) => {
    const dialogo = document.getElementById(botao.dataset.abrirModelo)
    // Navegador sem <dialog>: o botão some e a lista de peças do cartão continua valendo
    if (!dialogo || typeof dialogo.showModal !== 'function') {
      botao.hidden = true
      return
    }
    const abrir = dialogo.abrirModelo || (dialogo.abrirModelo = prepararModelo(dialogo))
    botao.addEventListener('click', abrir)
  })
})()
