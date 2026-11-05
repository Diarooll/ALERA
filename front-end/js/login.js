const DESTINOS = { admin: 'admin.html', morador: 'app.html' }
const ERRO_CONEXAO = 'Não foi possível conectar ao servidor. Tente de novo em instantes.'
const ERRO_TENTATIVAS = 'Muitas tentativas. Aguarde um minuto e tente de novo.'

function enviar(rota, dados) {
  return fetch(`${API_URL}${rota}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  })
}

const REGEX_EMAIL = /^\S+@\S+\.\S+$/
// DDD + número fixo (8 dígitos) ou celular (9 + 8 dígitos)
const REGEX_TELEFONE = /^[1-9]{2}9?\d{8}$/

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

function formatarTelefone(valor) {
  const digitos = valor.replace(/^\s*\+55/, '').replace(/\D/g, '').slice(0, 11)

  if (!digitos) return ''
  if (digitos.length <= 2) return `(${digitos}`

  const ddd = digitos.slice(0, 2)
  const numero = digitos.slice(2)

  if (numero.length <= 4) return `(${ddd}) ${numero}`

  const corte = numero.length === 9 ? 5 : 4
  return `(${ddd}) ${numero.slice(0, corte)}-${numero.slice(corte)}`
}

const campoTelefone = document.querySelector('#cadastro-phone')

campoTelefone.addEventListener('input', () => {
  // mantém o cursor no mesmo dígito ao editar no meio do número
  const digitosAntes = campoTelefone.value
    .slice(0, campoTelefone.selectionStart)
    .replace(/\D/g, '').length

  campoTelefone.value = formatarTelefone(campoTelefone.value)

  let posicao = 0
  let vistos = 0

  while (vistos < digitosAntes && posicao < campoTelefone.value.length) {
    if (/\d/.test(campoTelefone.value[posicao])) vistos++
    posicao++
  }

  campoTelefone.setSelectionRange(posicao, posicao)
})

function validarTelefone(telefone) {
  const digitos = telefone.value.replace(/\D/g, '')

  if (!digitos) return 'Digite seu telefone com DDD.'
  if (!REGEX_TELEFONE.test(digitos)) return 'Telefone inválido. Exemplo: (32) 99999-0000'
  return ''
}

function validarEndereco(endereco) {
  const valor = endereco.value.trim()

  if (!valor) return 'Digite seu endereço.'
  if (valor.length < 8) return 'Informe rua, número, bairro e cidade.'
  return ''
}

function validarConsentimento(consentimento) {
  return consentimento.checked ? '' : 'Marque a caixa para concordar e criar sua conta.'
}

function configurarFormulario(form, regras, aoSucesso) {
  form.addEventListener('submit', async (evento) => {
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

    const saindo = await aoSucesso()

    if (!saindo) {
      botao.disabled = false
      botao.classList.remove('carregando')
      texto.textContent = original
    }
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
  async () => {
    let mensagem = ERRO_CONEXAO

    try {
      const resposta = await enviar('/auth/login/', {
        email: loginEmail.value.trim().toLowerCase(),
        password: loginSenha.value,
      })

      if (resposta.ok) {
        const { token, papel } = await resposta.json()

        localStorage.setItem('token', token)
        localStorage.setItem('papel', papel)
        window.location.href = DESTINOS[papel]
        return true
      }

      if (resposta.status === 401) mensagem = 'E-mail ou senha incorretos.'
      if (resposta.status === 429) mensagem = ERRO_TENTATIVAS
    } catch {
      // sem resposta do servidor: fica o ERRO_CONEXAO
    }

    mostrarErro(loginSenha, mensagem)
    loginSenha.focus()
    return false
  },
)

const cadastroForm = document.querySelector('[data-form="cadastro"]')
const cadastroEmail = document.querySelector('#cadastro-email')
const cadastroSenha = document.querySelector('#cadastro-password')
const cadastroEndereco = document.querySelector('#cadastro-address')
const cadastroConsentimento = document.querySelector('#cadastro-consent')
// Nome de cada campo na resposta da API
const CAMPOS_CADASTRO = {
  email: cadastroEmail,
  senha: cadastroSenha,
  telefone: campoTelefone,
  endereco: cadastroEndereco,
  consentimento: cadastroConsentimento,
}

configurarFormulario(
  cadastroForm,
  [
    [cadastroEmail, validarEmail],
    [cadastroSenha, validarSenhaCadastro],
    [campoTelefone, validarTelefone],
    [cadastroEndereco, validarEndereco],
    [cadastroConsentimento, validarConsentimento],
  ],
  async () => {
    let mensagem = ERRO_CONEXAO

    try {
      const resposta = await enviar('/auth/cadastro/', {
        email: cadastroEmail.value.trim(),
        senha: cadastroSenha.value,
        telefone: campoTelefone.value,
        endereco: cadastroEndereco.value.trim(),
        consentimento: cadastroConsentimento.checked,
      })

      if (resposta.ok) {
        alert('Conta criada! Agora é só entrar com seu e-mail e sua senha.')
        cadastroForm.reset()
        location.hash = '#login'
        return false
      }

      if (resposta.status === 400) {
        const erros = await resposta.json()
        const campos = Object.keys(CAMPOS_CADASTRO).filter((nome) => erros[nome])

        campos.forEach((nome) => mostrarErro(CAMPOS_CADASTRO[nome], erros[nome][0]))

        if (campos.length) {
          CAMPOS_CADASTRO[campos[0]].focus()
          return false
        }
      }

      if (resposta.status === 429) mensagem = ERRO_TENTATIVAS
    } catch {
      // sem resposta do servidor: fica o ERRO_CONEXAO
    }

    // Erro que não é de um campo: aparece logo acima do botão
    mostrarErro(cadastroConsentimento, mensagem)
    return false
  },
)

// Modo teste: só aparece neste computador (ver api.js) e não fala com o servidor
const blocoTeste = document.querySelector('#modo-teste')

if (MODO_TESTE_DISPONIVEL && blocoTeste) {
  blocoTeste.hidden = false

  blocoTeste.querySelectorAll('[data-teste]').forEach((botao) => {
    botao.addEventListener('click', () => {
      const papel = botao.dataset.teste
      localStorage.setItem('token', 'modo-teste')
      localStorage.setItem('papel', papel)
      localStorage.setItem('modoTeste', '1')
      window.location.href = DESTINOS[papel]
    })
  })
}
