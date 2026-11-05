// Trava do app: só entra quem fez login. O servidor confirma; o navegador sozinho não decide.

function encerrarSessao() {
  localStorage.removeItem('token')
  localStorage.removeItem('papel')
  localStorage.removeItem('modoTeste')
}

// Se o servidor não confirmar o login, por qualquer motivo, a pessoa volta para o login.
async function conferirLogin() {
  if (modoTesteAtivo()) return

  try {
    const resposta = await fetch(`${API_URL}/me/`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })

    if (resposta.ok) return
  } catch {
    // sem resposta do servidor: trata como não confirmado
  }

  encerrarSessao()
  location.replace('login.html')
}

document.querySelector('#sair').addEventListener('click', encerrarSessao)

// pageshow também cobre o botão Voltar, que pode reabrir o app da memória sem rodar o <head>
window.addEventListener('pageshow', conferirLogin)
