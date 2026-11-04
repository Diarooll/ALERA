const APP_URL = 'app.html'
const USUARIO_EXEMPLO = {
  email: 'adminalera@alera.com.br',
  senha: 'adminAlera',
}

const REGEX_EMAIL = /^\S+@\S+\.\S+$/

const telas = {
  login: document.querySelector('#view-login'),
  cadastro: document.querySelector('#view-cadastro'),
}

function mostrarTela() {
  const atual = location.hash === '#cadastro' ? 'cadastro' : 'login'

  telas.login.hidden = atual !== 'login'
  telas.cadastro.hidden = atual !== 'cadastro'
  document.title = telas[atual].dataset.titulo
}

window.addEventListener('hashchange', mostrarTela)
mostrarTela()

document.querySelectorAll('.toggle').forEach((botao) => {
  botao.addEventListener('click', () => {
    const campo = botao.closest('.control').querySelector('input')
    const mostrar = campo.type === 'password'

    campo.type = mostrar ? 'text' : 'password'
    campo.classList.toggle('visivel', mostrar)

    botao.setAttribute('aria-pressed', mostrar)
    botao.setAttribute('aria-label', mostrar ? 'Ocultar senha' : 'Mostrar senha')
  })
})

function mostrarErro(campo, mensagem) {
  const erro = document.querySelector(`#${campo.id}-error`)

  campo.setAttribute('aria-invalid', 'true')
  erro.textContent = mensagem
  erro.hidden = false
}

function limparErro(campo) {
  const erro = document.querySelector(`#${campo.id}-error`)

  campo.removeAttribute('aria-invalid')
  erro.textContent = ''
  erro.hidden = true
}

document.querySelectorAll('.form input').forEach((campo) => {
  campo.addEventListener('input', () => limparErro(campo))
})

function validarEmail(email) {
  const valor = email.value.trim()

  if (!valor) return 'Digite seu e-mail.'
  if (!REGEX_EMAIL.test(valor)) return 'Digite um e-mail válido.'
  return ''
}

function validarSenhaLogin(senha) {
  return senha.value ? '' : 'Digite sua senha.'
}

function validarSenhaCadastro(senha) {
  if (!senha.value) return 'Crie uma senha.'
  if (senha.value.length < 8) return 'A senha precisa ter no mínimo 8 caracteres.'
  return ''
}

function validarEndereco(endereco) {
  const valor = endereco.value.trim()

  if (!valor) return 'Digite seu endereço.'
  if (valor.length < 8) return 'Informe rua, número, bairro e cidade.'
  return ''
}

function configurarFormulario(form, regras, aoSucesso) {
  form.addEventListener('submit', (evento) => {
    evento.preventDefault()

    let primeiroInvalido = null

    regras.forEach(([campo, validar]) => {
      const mensagem = validar(campo)

      if (mensagem) {
        mostrarErro(campo, mensagem)
        primeiroInvalido ??= campo
      } else {
        limparErro(campo)
      }
    })

    if (primeiroInvalido) {
      primeiroInvalido.focus()
      return
    }

    const botao = form.querySelector('.btn')
    const texto = botao.querySelector('.btn-label')
    const original = texto.textContent

    botao.disabled = true
    botao.classList.add('carregando')
    texto.textContent = 'Aguarde...'

    setTimeout(() => {
      const saindo = aoSucesso()

      if (!saindo) {
        botao.disabled = false
        botao.classList.remove('carregando')
        texto.textContent = original
      }
    }, 800)
  })
}

const loginEmail = document.querySelector('#login-email')
const loginSenha = document.querySelector('#login-password')

configurarFormulario(
  document.querySelector('[data-form="login"]'),
  [
    [loginEmail, validarEmail],
    [loginSenha, validarSenhaLogin],
  ],
  () => {
    const correto =
      loginEmail.value.trim().toLowerCase() === USUARIO_EXEMPLO.email &&
      loginSenha.value === USUARIO_EXEMPLO.senha

    if (correto) {
      sessionStorage.setItem('logado', 'true')
      window.location.href = APP_URL
      return true
    }

    mostrarErro(loginSenha, 'E-mail ou senha incorretos.')
    loginSenha.focus()
    return false
  },
)

const cadastroForm = document.querySelector('[data-form="cadastro"]')

configurarFormulario(
  cadastroForm,
  [
    [document.querySelector('#cadastro-email'), validarEmail],
    [document.querySelector('#cadastro-password'), validarSenhaCadastro],
    [document.querySelector('#cadastro-address'), validarEndereco],
  ],
  () => {
    alert('Conta criada com sucesso!')
    cadastroForm.reset()
    location.hash = '#login'
    return false
  },
)
