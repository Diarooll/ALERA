// ALERA · movimento.js
// Animações comuns ao site, ao login, ao app e ao painel. Sem bibliotecas de fora.
// Funciona junto com css/movimento.css. Como usar: docs/redesign/cartaz-de-rua.md
//
// No HTML:
//   data-revelar               o elemento sobe e aparece quando entra na tela
//   data-revelar="esquerda"    (ou "direita", "crescer") muda de onde ele vem
//   data-revelar-grupo         os filhos diretos entram um depois do outro
//   data-obturador             a foto de dentro abre como obturador (uma por página)
//   data-ima                   o botão é puxado de leve pelo mouse
//   data-deriva="0.15"         a foto anda devagar com a rolagem (0.1 a 0.3)
//   data-contar                o número conta do zero até o valor escrito (nunca em mortes)
//   class="pressionavel"       afunda ao apertar (só CSS)
//
// No JS das páginas:
//   Movimento.observar(raiz)   processa conteúdo novo (listas montadas depois do fetch)
//   Movimento.aviso(texto, { tipo: 'ok' | 'erro' | 'info', tempo: 3500 })
//   Movimento.tremer(elemento) tremidinha de erro (campo inválido, senha errada)
//   Movimento.vibrar(ms)       vibração curta no celular, se o aparelho deixar
//   Movimento.reduzido()       hoje sempre false: as animações rodam sempre (ver abaixo)

const Movimento = (() => {
  const raiz = document.documentElement
  // Decisão do dono do projeto: as animações rodam sempre, mesmo quando o sistema
  // pede "menos movimento" (Windows com efeitos de animação desligados, por exemplo).
  // Se um dia quiserem respeitar esse pedido, é só voltar para:
  // matchMedia('(prefers-reduced-motion: reduce)').matches
  const reduzido = () => false

  // A partir daqui, o CSS sabe que o script rodou e desliga a "segurança" de 2,5 s
  raiz.classList.add('movimento-pronto')

  // ---------- Entrada ao rolar ----------

  const vigiadoPor = new WeakMap() // moldura vigiada → elemento que anima

  const observador =
    'IntersectionObserver' in window
      ? new IntersectionObserver(
          (entradas) => {
            entradas.forEach((entrada) => {
              if (!entrada.isIntersecting) return
              // Para o obturador, quem é vigiado é a moldura (ver observar); quem anima é a foto
              const alvo = vigiadoPor.get(entrada.target) || entrada.target
              alvo.classList.add('revelado')
              observador.unobserve(entrada.target)
              if (alvo.hasAttribute('data-contar')) contar(alvo)
            })
          },
          // Dispara um pouco antes do fim da tela, para não ver o bloco "esperando"
          { rootMargin: '0px 0px -8% 0px', threshold: 0.12 },
        )
      : null

  function prepararGrupo(grupo) {
    ;[...grupo.children].forEach((filho, i) => filho.style.setProperty('--ordem', i))
  }

  function observar(base = document) {
    const alvos = base.querySelectorAll(
      '[data-revelar]:not(.revelado), [data-revelar-grupo]:not(.revelado), [data-obturador]:not(.revelado), [data-contar]:not(.contado)',
    )
    alvos.forEach((alvo) => {
      if (alvo.hasAttribute('data-revelar-grupo')) prepararGrupo(alvo)
      // O obturador começa com clip-path em 100%: para o navegador ele tem área visível zero
      // e nunca "entra na tela". Por isso vigiamos a moldura dele (o elemento pai)
      let vigiado = alvo
      if (alvo.hasAttribute('data-obturador') && alvo.parentElement) {
        vigiado = alvo.parentElement
        vigiadoPor.set(vigiado, alvo)
      }
      if (observador && !reduzido()) observador.observe(vigiado)
      else {
        alvo.classList.add('revelado')
        if (alvo.hasAttribute('data-contar')) alvo.classList.add('contado')
      }
    })
    if (!reduzido()) ligarIma(base)
  }

  // ---------- Contagem de números ----------
  // O número final já está escrito no HTML (quem não tem script vê o certo).
  // Aceita "8.854", "128 mil", "250 t": conta só a parte numérica e mantém o resto.

  const formato = new Intl.NumberFormat('pt-BR')

  function contar(el) {
    if (el.classList.contains('contado')) return
    el.classList.add('contado')
    if (reduzido()) return

    const original = el.textContent
    const achado = original.match(/\d[\d.]*/)
    if (!achado) return
    const final = Number(achado[0].replace(/\./g, ''))
    const antes = original.slice(0, achado.index)
    const depois = original.slice(achado.index + achado[0].length)
    const duracao = Math.min(1600, 600 + final / 8)
    const inicio = performance.now()

    // Leitor de tela lê o valor final, não os números passando
    el.setAttribute('aria-label', original.trim())

    function quadro(agora) {
      const t = Math.min(1, (agora - inicio) / duracao)
      const suave = 1 - Math.pow(1 - t, 4)
      el.textContent = antes + formato.format(Math.round(final * suave)) + depois
      if (t < 1) requestAnimationFrame(quadro)
      else el.textContent = original
    }
    requestAnimationFrame(quadro)
  }

  // ---------- Ímã (só com mouse) ----------

  const comMouse = matchMedia('(hover: hover) and (pointer: fine)')

  function ligarIma(base) {
    if (!comMouse.matches) return
    base.querySelectorAll('[data-ima]:not([data-ima-ligado])').forEach((el) => {
      el.setAttribute('data-ima-ligado', '')
      const forca = Number(el.dataset.ima) || 0.25
      el.addEventListener('pointermove', (evento) => {
        const caixa = el.getBoundingClientRect()
        const x = (evento.clientX - caixa.left - caixa.width / 2) * forca
        const y = (evento.clientY - caixa.top - caixa.height / 2) * forca
        el.style.setProperty('--ima-x', `${x.toFixed(1)}px`)
        el.style.setProperty('--ima-y', `${y.toFixed(1)}px`)
      })
      el.addEventListener('pointerleave', () => {
        el.style.setProperty('--ima-x', '0px')
        el.style.setProperty('--ima-y', '0px')
      })
    })
  }

  // ---------- Deriva com a rolagem ----------

  let derivas = []
  let agendado = false

  function atualizarDerivas() {
    agendado = false
    const altura = innerHeight
    derivas.forEach((el) => {
      const caixa = el.getBoundingClientRect()
      if (caixa.bottom < -200 || caixa.top > altura + 200) return
      const meio = caixa.top + caixa.height / 2 - altura / 2
      const fator = Number(el.dataset.deriva) || 0.15
      el.style.setProperty('--deriva', `${(-meio * fator).toFixed(1)}px`)
    })
  }

  function ligarDerivas() {
    derivas = [...document.querySelectorAll('[data-deriva]')]
    if (!derivas.length || reduzido()) return
    addEventListener(
      'scroll',
      () => {
        if (agendado) return
        agendado = true
        requestAnimationFrame(atualizarDerivas)
      },
      { passive: true },
    )
    atualizarDerivas()
  }

  // ---------- Avisos rápidos ----------

  let caixaAvisos = null

  function aviso(texto, { tipo = 'info', tempo = 3500 } = {}) {
    if (!caixaAvisos) {
      caixaAvisos = document.createElement('div')
      caixaAvisos.className = 'avisos'
      caixaAvisos.setAttribute('role', 'status')
      caixaAvisos.setAttribute('aria-live', 'polite')
      document.body.append(caixaAvisos)
    }
    const item = document.createElement('div')
    item.className = 'aviso'
    item.dataset.tipo = tipo
    item.textContent = texto // textContent: nunca HTML vindo de fora
    caixaAvisos.append(item)

    setTimeout(() => {
      item.classList.add('saindo')
      setTimeout(() => item.remove(), reduzido() ? 0 : 260)
    }, tempo)
    return item
  }

  // ---------- Tremidinha e vibração ----------

  function tremer(el) {
    if (!el) return
    el.classList.remove('tremendo')
    void el.offsetWidth // reinicia a animação se tremer duas vezes seguidas
    el.classList.add('tremendo')
    el.addEventListener('animationend', () => el.classList.remove('tremendo'), { once: true })
    vibrar([12, 40, 12])
  }

  function vibrar(padrao = 10) {
    if (reduzido() || !('vibrate' in navigator)) return
    try {
      navigator.vibrate(padrao)
    } catch {
      // alguns navegadores bloqueiam sem gesto do usuário: tudo bem
    }
  }

  // ---------- Começo ----------

  function iniciar() {
    observar(document)
    ligarDerivas()
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar)
  else iniciar()

  return { observar, aviso, tremer, vibrar, reduzido }
})()
