// ALERA · site.js
// Scripts do site (index.html). O site funciona sem eles: as cores dos níveis e a
// mensagem trocam só com CSS. Aqui ficam três coisas a mais:
//   1. o nome da rua digitado entra na mensagem (sempre por textContent)
//   2. a chuva desenhada no <canvas>, mais forte a cada nível
//   3. os painéis de "Como funciona" nunca ficam todos fechados

;(() => {
  const pedeMenos = matchMedia('(prefers-reduced-motion: reduce)')

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

  const secao = document.querySelector('.sua-rua')
  const tela = document.querySelector('.chuva')
  const radios = document.querySelectorAll('.nivel-radio')

  // Quanto chove em cada nível (0 a 1)
  const FORCA = { normal: 0.12, atencao: 0.38, alerta: 0.68, perigo: 1 }
  const MAX_GOTAS = 240

  let forcaAlvo = FORCA.alerta
  let forcaAtual = forcaAlvo

  function nivelMarcado() {
    const marcado = document.querySelector('.nivel-radio:checked')
    return marcado ? marcado.value : 'alerta'
  }

  if (secao && tela && tela.getContext) {
    const ctx = tela.getContext('2d')
    const gotas = []
    let largura = 0
    let altura = 0
    let visivel = false
    let quadro = 0

    function novaGota(espalhar) {
      return {
        x: Math.random() * (largura + 200) - 100,
        y: espalhar ? Math.random() * altura : -40 - Math.random() * altura * 0.3,
        tam: 14 + Math.random() * 22,
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
      // A chuva usa a cor do texto do nível (escura nos claros, branca no vermelho)
      ctx.strokeStyle = getComputedStyle(secao).color
      ctx.globalAlpha = 0.28 + forcaAtual * 0.17
      ctx.lineWidth = 1.5 + forcaAtual
      ctx.lineCap = 'round'
      const quantas = Math.round(MAX_GOTAS * forcaAtual)
      const vento = 0.12 + forcaAtual * 0.18 // gota inclinada: mais vento, mais inclinada
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

    const rodando = () => visivel && !document.hidden && !pedeMenos.matches

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

    // Só chove quando a seção está na tela e a aba está aberta
    if ('IntersectionObserver' in window) {
      new IntersectionObserver((entradas) => {
        visivel = entradas[0].isIntersecting
        ligar()
      }).observe(secao)
    } else {
      visivel = true
    }
    document.addEventListener('visibilitychange', ligar)
    pedeMenos.addEventListener('change', () => {
      forcaAtual = forcaAlvo
      desenhar(0)
      ligar()
    })

    if ('ResizeObserver' in window) new ResizeObserver(medir).observe(secao)
    else addEventListener('resize', medir)

    forcaAlvo = FORCA[nivelMarcado()] ?? FORCA.alerta
    forcaAtual = forcaAlvo
    medir()
    ligar()

    radios.forEach((radio) =>
      radio.addEventListener('change', () => {
        forcaAlvo = FORCA[radio.value] ?? FORCA.alerta
        // Quem pediu menos movimento vê a chuva parada, já na força nova
        if (pedeMenos.matches) {
          forcaAtual = forcaAlvo
          desenhar(0)
        }
        if (window.Movimento) Movimento.vibrar(radio.value === 'perigo' ? [20, 40, 20] : 10)
      }),
    )
  }

  // ---------- 3. Painéis de "Como funciona" ----------

  const paineis = [...document.querySelectorAll('.painel details')]
  paineis.forEach((painel) => {
    const resumo = painel.querySelector('summary')
    // Clicar no painel aberto não fecha: sempre fica um passo à mostra
    resumo.addEventListener('click', (evento) => {
      if (painel.open) evento.preventDefault()
    })
    // Navegador sem <details name>: fecha os outros na mão
    painel.addEventListener('toggle', () => {
      if (!painel.open) return
      paineis.forEach((outro) => {
        if (outro !== painel) outro.open = false
      })
    })
  })
})()
