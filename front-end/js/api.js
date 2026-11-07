// A página roda neste computador (arquivo aberto ou localhost)?
const LOCAL = location.protocol === 'file:' || ['localhost', '127.0.0.1'].includes(location.hostname)

// Endereço do back-end. No computador, o Django do manage.py runserver. Publicado, a Cloudflare
// passa /api/* para o Django no mesmo domínio. Se a API for morar em outro endereço, trocar aqui
const API_URL = LOCAL ? 'http://127.0.0.1:8000/api' : '/api'

// Modo teste: deixa abrir o app e o painel sem o servidor, só para testar o visual.
// Só existe quando a página roda neste computador; em qualquer site publicado ele não
// aparece e não vale. Não dá acesso a dado nenhum.
const MODO_TESTE_DISPONIVEL = LOCAL

function modoTesteAtivo() {
  try {
    return MODO_TESTE_DISPONIVEL && localStorage.getItem('modoTeste') === '1'
  } catch {
    return false
  }
}

// ---------- sessão ----------
// "token" vence em 20 minutos; "renovacao" troca por um par novo sem pedir a senha
// (30 dias para morador, 12 horas para administrador, contados de novo a cada troca).
// Com "Continuar conectado" a sessão fica no localStorage e sobrevive a fechar o navegador;
// sem, fica no sessionStorage e some quando a aba fecha. guarda.js lê as mesmas chaves
const CHAVES_SESSAO = ['token', 'renovacao', 'papel', 'tokenVenceEm', 'modoTeste']
// Renova quando falta menos que isto, para o pedido não chegar com o token já vencido
const FOLGA_PARA_RENOVAR_MS = 60 * 1000

function armazem(manter) {
  try {
    return manter ? window.localStorage : window.sessionStorage
  } catch {
    return null // navegador bloqueando o armazenamento
  }
}

// O meio do JWT é um JSON em base64. Só lê: quem confere a assinatura é o servidor
function lerJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

function lerDe(guardado) {
  try {
    const token = guardado?.getItem('token')
    if (!token) return null
    return {
      token,
      renovacao: guardado.getItem('renovacao'),
      papel: guardado.getItem('papel'),
      venceEm: Number(guardado.getItem('tokenVenceEm')) || 0,
    }
  } catch {
    return null
  }
}

function limparDe(guardado) {
  try {
    CHAVES_SESSAO.forEach((chave) => guardado?.removeItem(chave))
  } catch {
    // bloqueado: não tem o que limpar
  }
}

// { token, renovacao, papel, venceEm, manter } de quem entrou, ou null.
// A da aba (sessionStorage) vem antes: foi escolhida para esta aba
function lerSessao() {
  for (const manter of [false, true]) {
    const sessao = lerDe(armazem(manter))
    if (sessao) return { ...sessao, manter }
  }
  return null
}

// Guarda a sessão de um login de verdade (ou de uma renovação). Também encerra o modo teste
function salvarSessao({ token, renovacao, papel }, manter = true) {
  const jwt = lerJwt(token)
  // O vencimento vai no relógio deste aparelho: um relógio adiantado não faz renovar à toa
  const venceEm = jwt?.exp && jwt?.iat ? Date.now() + (jwt.exp - jwt.iat) * 1000 : 0
  const valores = { token, renovacao, papel, tokenVenceEm: venceEm ? String(venceEm) : '', modoTeste: '' }
  const destino = armazem(manter)

  limparDe(armazem(!manter)) // a sessão fica num lugar só
  // Escreve por cima, sem apagar antes: as outras abas nunca veem o token sumir no meio da troca
  Object.entries(valores).forEach(([chave, valor]) => {
    if (valor) destino.setItem(chave, valor)
    else destino.removeItem(chave)
  })
}

function limparSessao() {
  limparDe(armazem(true))
  limparDe(armazem(false))
}

// O servidor disse outro papel (a conta mudou): guarda, para o login mandar ao lugar certo
function guardarPapel(papel) {
  const sessao = lerSessao()
  try {
    if (sessao) armazem(sessao.manter).setItem('papel', papel)
  } catch {
    // bloqueado: o servidor confere de novo na próxima página
  }
}

// Tem sessão que ainda pode valer. Quem confirma é o servidor, no primeiro pedido
function temSessao() {
  const sessao = lerSessao()
  if (!sessao) return false
  if (modoTesteAtivo()) return true
  const vence = lerJwt(sessao.renovacao || sessao.token)?.exp
  return Boolean(vence) && vence * 1000 > Date.now()
}

function quaseVencido(sessao) {
  return Boolean(sessao.venceEm) && Date.now() > sessao.venceEm - FOLGA_PARA_RENOVAR_MS
}

// Servidor travado não pode prender a renovação (e a trava entre abas) para sempre
function tempoLimite(ms) {
  const controle = new AbortController()
  setTimeout(() => controle.abort(), ms)
  return controle.signal
}

function postar(rota, dados, ms, keepalive = false) {
  return fetch(`${API_URL}${rota}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
    signal: tempoLimite(ms),
    keepalive,
  })
}

// Uma renovação por vez. Cada token de renovação só vale uma vez (o servidor gira e põe o
// usado na lista negra): duas renovações com o mesmo token, de duas abas ou de vários pedidos
// juntos, fariam a segunda dar 401 e derrubar a sessão. Na aba, todos esperam a mesma promessa
let renovacaoEmCurso = null

function renovarSessao(tokenVelho) {
  renovacaoEmCurso ??= comTrava(() => renovarAgora(tokenVelho)).finally(() => {
    renovacaoEmCurso = null
  })
  return renovacaoEmCurso
}

// Entre abas, a trava do navegador. Onde ela não existe (navegador antigo, página aberta
// pelo arquivo), segue sem: renovarAgora ainda confere se outra aba já renovou antes de derrubar
async function comTrava(tarefa) {
  if (!navigator.locks?.request) return tarefa()
  let entrou = false
  try {
    return await navigator.locks.request('alera-renovar', () => {
      entrou = true
      return tarefa()
    })
  } catch (erro) {
    if (entrou) throw erro
    return tarefa()
  }
}

// Devolve o token novo, ou null quando a sessão acabou de verdade.
// Lança erro quando só não deu agora (sem internet, servidor fora): aí ninguém é derrubado
async function renovarAgora(tokenVelho) {
  // Relê aqui dentro: enquanto esta aba esperava a trava, outra pode ter renovado ou saído
  const sessao = lerSessao()
  if (!sessao) return null
  if (sessao.token !== tokenVelho && !quaseVencido(sessao)) return sessao.token
  if (!sessao.renovacao) return null // sessão de antes da renovação existir

  const resposta = await postar('/auth/renovar/', { renovacao: sessao.renovacao }, 10000)

  if (resposta.ok) {
    const { token, renovacao } = await resposta.json()
    // Saiu da conta enquanto a renovação ia e voltava: continua fora
    if (!lerSessao()) {
      postar('/auth/sair/', { renovacao }, 5000).catch(() => {})
      return null
    }
    salvarSessao({ token, renovacao, papel: sessao.papel }, sessao.manter)
    return token
  }

  if (resposta.status === 401) {
    // Antes de derrubar, confere se outra aba girou o token no meio do caminho
    const atual = lerSessao()
    if (atual && atual.renovacao !== sessao.renovacao) return atual.token
    limparSessao()
    return null
  }

  // 429, 500, servidor reiniciando: não é a sessão que acabou
  throw new Error(`renovação recusada: ${resposta.status}`)
}

function pedir(rota, metodo, corpo, token) {
  const cabecalhos = {}
  if (token) cabecalhos.Authorization = `Bearer ${token}`
  if (corpo !== undefined) cabecalhos['Content-Type'] = 'application/json'

  return fetch(`${API_URL}${rota}`, {
    method: metodo,
    headers: cabecalhos,
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  })
}

// Chamada à API já com o token de quem está logado. Renova sozinha: antes, se o token está
// para vencer; depois, se veio 401 (renova uma vez e repete o pedido). Só devolve 401 quando
// a sessão acabou de verdade, e aí quem chama manda para o login. Se não deu para renovar por
// falta de conexão, lança erro como um fetch sem rede: a pessoa vê o aviso e continua logada
async function chamarApi(rota, { metodo = 'GET', corpo } = {}) {
  // Modo teste não fala com o servidor: quem chama cai no aviso de "sem conexão"
  if (modoTesteAtivo()) throw new Error('modo teste: sem servidor')

  const sessao = lerSessao()
  let token = sessao?.token

  if (sessao?.renovacao && quaseVencido(sessao)) {
    try {
      token = (await renovarSessao(token)) ?? token
    } catch {
      // sem servidor agora: tenta o pedido com o token que tem
    }
  }

  const resposta = await pedir(rota, metodo, corpo, token)
  // O 401 vem antes de o servidor fazer qualquer coisa, então repetir o pedido é seguro
  if (resposta.status !== 401 || !sessao) return resposta

  const novo = await renovarSessao(token)
  return novo ? pedir(rota, metodo, corpo, novo) : resposta
}

// Sair: apaga a sessão deste navegador na hora e avisa o servidor para o token de renovação
// parar de valer. keepalive deixa o aviso seguir mesmo com a página indo embora.
// Com o servidor fora, sai do mesmo jeito: espera no máximo 3 segundos
async function sairDaConta() {
  const sessao = modoTesteAtivo() ? null : lerSessao()
  limparSessao()
  if (!sessao?.renovacao) return

  try {
    await postar('/auth/sair/', { renovacao: sessao.renovacao }, 3000, true)
  } catch {
    // sem conexão: o token some deste aparelho e vence sozinho
  }
}
