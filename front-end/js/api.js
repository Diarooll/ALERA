// Endereço do back-end. Trocar aqui quando a API estiver hospedada.
const API_URL = 'http://127.0.0.1:8000/api'

// Modo teste: deixa abrir o app e o painel sem o servidor, só para testar o visual.
// Só existe quando a página roda neste computador (arquivo aberto ou localhost);
// em qualquer site publicado ele não aparece e não vale. Não dá acesso a dado nenhum.
const MODO_TESTE_DISPONIVEL =
  location.protocol === 'file:' || ['localhost', '127.0.0.1'].includes(location.hostname)

function modoTesteAtivo() {
  try {
    return MODO_TESTE_DISPONIVEL && localStorage.getItem('modoTeste') === '1'
  } catch {
    return false
  }
}

// Chamada à API já com o token de quem está logado. Quem chama trata o 401 (sessão vencida).
function chamarApi(rota, { metodo = 'GET', corpo } = {}) {
  const cabecalhos = { Authorization: `Bearer ${localStorage.getItem('token')}` }
  if (corpo !== undefined) cabecalhos['Content-Type'] = 'application/json'

  return fetch(`${API_URL}${rota}`, {
    method: metodo,
    headers: cabecalhos,
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  })
}
