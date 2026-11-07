// ALERA · tema.js
// Claro ou escuro, igual no site, no login, no app e no painel.
// Carregar no <head>, SEM defer: assim o tema certo entra antes da primeira pintura
// e a página não pisca branca para quem usa o escuro.
//
// Como funciona:
// - A escolha fica em localStorage.tema ('claro' ou 'escuro'). Sem escolha, segue o sistema.
// - O <html> recebe data-tema="claro" ou "escuro". O CSS escuro deve usar
//   :root[data-tema="escuro"] (e pode manter :root:has(#tema:checked) para quem não tem JS).
// - O botão continua sendo o checkbox #tema. Ao trocar, a cor nova abre em círculo
//   a partir do botão (View Transitions; quem não tem só troca).

;(() => {
  const raiz = document.documentElement
  const sistemaEscuro = matchMedia('(prefers-color-scheme: dark)')

  function lerEscolha() {
    try {
      return localStorage.getItem('tema')
    } catch {
      return null
    }
  }

  function temaAtual() {
    return lerEscolha() || (sistemaEscuro.matches ? 'escuro' : 'claro')
  }

  function aplicar(tema) {
    raiz.dataset.tema = tema
    const caixa = document.querySelector('#tema')
    if (caixa) caixa.checked = tema === 'escuro'
    // A barra do navegador no celular acompanha o fundo
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) meta.content = tema === 'escuro' ? '#111827' : '#1E2A5A'
  }

  aplicar(temaAtual())

  // Se a pessoa nunca escolheu, acompanha a troca do sistema (ex.: celular que escurece à noite)
  sistemaEscuro.addEventListener('change', () => {
    if (!lerEscolha()) aplicar(temaAtual())
  })

  function ligarBotao() {
    const caixa = document.querySelector('#tema')
    if (!caixa) return
    caixa.checked = raiz.dataset.tema === 'escuro'

    caixa.addEventListener('change', () => {
      const novo = caixa.checked ? 'escuro' : 'claro'
      try {
        localStorage.setItem('tema', novo)
      } catch {
        // navegação privada sem storage: troca só nesta página
      }

      const semAnimacao =
        !document.startViewTransition || matchMedia('(prefers-reduced-motion: reduce)').matches
      if (semAnimacao) return aplicar(novo)

      // O círculo nasce no meio do botão e cresce até cobrir a tela inteira
      const botao = document.querySelector(`label[for="tema"]`) || caixa
      const caixaBotao = botao.getBoundingClientRect()
      const x = caixaBotao.left + caixaBotao.width / 2
      const y = caixaBotao.top + caixaBotao.height / 2
      const raio = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))

      // .trocando-tema desliga a animação de troca de página (movimento.css) durante o círculo
      raiz.classList.add('trocando-tema')
      const transicao = document.startViewTransition(() => aplicar(novo))
      transicao.finished.finally(() => raiz.classList.remove('trocando-tema'))
      transicao.ready.then(() => {
        raiz.animate(
          { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${raio}px at ${x}px ${y}px)`] },
          {
            duration: 620,
            easing: 'cubic-bezier(.16, 1, .3, 1)',
            pseudoElement: '::view-transition-new(root)',
          },
        )
      })
    })
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ligarBotao)
  else ligarBotao()
})()
