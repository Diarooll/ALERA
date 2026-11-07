// Tranca do <head> do app e do painel: nem mostra a página a quem não entrou.
// Carrega sem defer, antes do CSS, para rodar antes de a página aparecer.
// Quem confirma de verdade é o servidor, na conferência de app.js e admin.js.
// Fica num arquivo (e não dentro do HTML) para as páginas poderem proibir script inline.
//
// A sessão fica no sessionStorage (só esta aba) ou no localStorage ("Continuar conectado"),
// com as mesmas chaves do api.js. A da aba vale primeiro, como no lerSessao().
// O modo teste também guarda "token" e "papel" no localStorage, então passa igual.

// Entre chaves para nada daqui virar global e esbarrar nos outros scripts da página
{
  const paginaDoAdmin = /admin\.html$/.test(location.pathname)

  const sessaoGuardada = () => {
    const guardado = sessionStorage.getItem('token') ? sessionStorage : localStorage
    return guardado.getItem('token') ? guardado : null
  }

  try {
    const guardado = sessaoGuardada()

    if (!guardado) location.replace('login.html')
    // Morador no painel vai para o login, que já o manda para o app dele
    else if (paginaDoAdmin && guardado.getItem('papel') !== 'admin') location.replace('login.html')
  } catch {
    // Navegador bloqueando o armazenamento: sem como guardar a sessão
    location.replace('login.html')
  }

  // Saiu da conta em outra aba: esta vai junto para o login. Só o localStorage avisa as
  // outras abas. Token trocado por outro é renovação; só conta o token apagado (ou tudo limpo)
  window.addEventListener('storage', (evento) => {
    if (evento.key !== null && (evento.key !== 'token' || evento.newValue)) return
    try {
      if (!sessaoGuardada()) location.replace('login.html')
    } catch {
      location.replace('login.html')
    }
  })
}
