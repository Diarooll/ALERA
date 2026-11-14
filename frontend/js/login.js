const DESTINOS = { admin: 'admin.html', morador: 'app.html' }
const ERRO_CONEXAO = 'Não foi possível conectar ao servidor. Tente de novo em instantes.'
const ERRO_TENTATIVAS = 'Muitas tentativas. Aguarde um minuto e tente de novo.'

// Já entrou neste aparelho: vai direto para a sua tela, sem pedir a senha de novo
function irSeJaEntrou() {
  const destino = temSessao() && DESTINOS[lerSessao().papel]
  if (destino) location.replace(destino)
}

irSeJaEntrou()
// O botão Voltar pode reabrir o login da memória, sem rodar o script de novo
window.addEventListener('pageshow', (evento) => evento.persisted && irSeJaEntrou())

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
const manchete = document.querySelector('#manchete')
const fraseCartaz = document.querySelector('#cartaz-frase')
let telaAtual = null

// Só muda o texto se mudou: assim o leitor de tela não repete a mesma frase
function dizer(elemento, texto) {
  if (elemento.textContent !== texto) elemento.textContent = texto
}

// A manchete do cartaz. No cadastro ela vira o nome da rua, que vem do ViaCEP ou da
// pessoa: por isso textContent. A classe pelo tamanho segura o nome em duas linhas
function trocarManchete(texto, frase) {
  if (frase) dizer(fraseCartaz, frase)
  if (manchete.textContent === texto) return

  manchete.textContent = texto
  manchete.classList.toggle('manchete--longa', texto.length > 22 && texto.length <= 34)
  manchete.classList.toggle('manchete--muito-longa', texto.length > 34)

  if (!Movimento.reduzido()) {
    manchete.animate(
      [
        { clipPath: 'inset(0 0 100% 0)', transform: 'translateY(0.3em)' },
        { clipPath: 'inset(0 0 0 0)', transform: 'none' },
      ],
      { duration: 560, easing: 'cubic-bezier(.16, 1, .3, 1)' },
    )
  }
}

// Na tela de cadastro, a manchete é a rua da pessoa assim que ela existir
function manchetePara(tela) {
  const rua = tela === 'cadastro' && cadastroRua.value.trim()
  return rua || telas[tela].dataset.manchete
}

// Login ou cadastro pelo #cadastro na URL (o link "Criar conta" só troca o hash)
function mostrarTela() {
  const atual = location.hash === '#cadastro' ? 'cadastro' : 'login'
  if (atual === telaAtual) return

  const primeiraVez = telaAtual === null
  telaAtual = atual

  if (atual === 'cadastro' && !blocoPronto.hidden) recomecarCadastro()

  telas.login.hidden = atual !== 'login'
  telas.cadastro.hidden = atual !== 'cadastro'
  document.title = telas[atual].dataset.titulo
  trocarManchete(manchetePara(atual), telas[atual].dataset.frase)

  if (!primeiraVez) {
    const tela = telas[atual]
    if (!Movimento.reduzido()) {
      tela.animate(
        [
          { opacity: 0, transform: 'translateY(16px)' },
          { opacity: 1, transform: 'none' },
        ],
        { duration: 420, easing: 'cubic-bezier(.16, 1, .3, 1)' },
      )
    }
    tela.querySelector('.tela-titulo').focus()
  }
}

// Olho de mostrar/ocultar: o CSS anima o risco sumindo e a pupila abrindo
document.querySelectorAll('.olho').forEach((botao) => {
  botao.addEventListener('click', () => {
    const campo = botao.closest('.caixa').querySelector('input')
    const mostrar = campo.type === 'password'

    campo.type = mostrar ? 'text' : 'password'
    botao.setAttribute('aria-pressed', mostrar)
    botao.setAttribute('aria-label', mostrar ? 'Ocultar senha' : 'Mostrar senha')
  })
})

function mostrarErro(campo, mensagem) {
  const erro = document.querySelector(`#${campo.id}-error`)
  if (!erro) return

  campo.setAttribute('aria-invalid', 'true')
  erro.textContent = mensagem
  erro.hidden = false
  Movimento.tremer(campo.closest('.campo') || campo.closest('.marcar'))
}

function limparErro(campo) {
  const erro = document.querySelector(`#${campo.id}-error`)
  if (!erro) return // campo sem mensagem de erro (complemento, caixinhas)

  campo.removeAttribute('aria-invalid')
  erro.textContent = ''
  erro.hidden = true
}

document.querySelectorAll('.formulario input').forEach((campo) => {
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

// Força da senha, nos quatro níveis do alerta: 1 vermelho, 2 laranja, 3 amarelo, 4 verde.
// O texto diz o que falta, não só o nome do nível
const SENHAS_COMUNS = ['12345678', '123456789', '1234567890', '87654321', 'senha123', 'password', 'qwerty123', 'abcd1234', 'alera123']

function avaliarSenha(senha) {
  if (!senha) return { nivel: 0, texto: 'Use no mínimo 8 caracteres.' }

  if (senha.length < 8) {
    const faltam = 8 - senha.length
    return { nivel: 1, texto: `Curta demais: ${faltam === 1 ? 'falta 1 caractere' : `faltam ${faltam} caracteres`}.` }
  }

  if (SENHAS_COMUNS.includes(senha.toLowerCase()) || /^(.)\1+$/.test(senha)) {
    return { nivel: 1, texto: 'Fraca: essa senha é fácil de adivinhar. Tente outra.' }
  }

  let pontos = 0
  if (/[a-z]/.test(senha) && /[A-Z]/.test(senha)) pontos++
  if (/\d/.test(senha)) pontos++
  if (/[^A-Za-z0-9]/.test(senha)) pontos++
  if (senha.length >= 12) pontos++

  if (pontos === 0) return { nivel: 1, texto: 'Fraca: só letras é fácil de adivinhar. Junte números ou símbolos.' }
  if (pontos === 1) return { nivel: 2, texto: 'Razoável: junte números, símbolos ou letras maiúsculas.' }
  if (pontos === 2) return { nivel: 3, texto: 'Boa: mais um símbolo ou uns caracteres a mais deixam forte.' }
  return { nivel: 4, texto: 'Forte: difícil de adivinhar.' }
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

const REGEX_CEP = /^\d{5}-?\d{3}$/

function validarCep(cep) {
  const valor = cep.value.trim()

  if (!valor) return 'Digite seu CEP.'
  if (!REGEX_CEP.test(valor)) return 'CEP inválido. Exemplo: 36010-000'
  return ''
}

function validarTexto(nome) {
  return (campo) => (campo.value.trim() ? '' : `Informe ${nome}.`)
}

function validarNumero(numero) {
  if (document.querySelector('#cadastro-nonumber').checked) return ''
  return numero.value.trim() ? '' : 'Digite o número ou marque "Minha casa não tem número".'
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
    texto.textContent = `${botao.dataset.carregando || 'Aguarde'}…`

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
        const dados = await resposta.json()
        // Sem a caixinha na página, vale o padrão: continuar conectado
        const manter = document.querySelector('#login-manter')?.checked ?? true

        salvarSessao(dados, manter)
        window.location.href = DESTINOS[dados.papel]
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
const cadastroCep = document.querySelector('#cadastro-cep')
const cadastroRua = document.querySelector('#cadastro-street')
const cadastroNumero = document.querySelector('#cadastro-number')
const cadastroSemNumero = document.querySelector('#cadastro-nonumber')
const cadastroBairro = document.querySelector('#cadastro-neighborhood')
const cadastroCidade = document.querySelector('#cadastro-city')
const cadastroConsentimento = document.querySelector('#cadastro-consent')
const cadastroComplemento = document.querySelector('#cadastro-complement')
// Nome de cada campo na resposta da API
const CAMPOS_CADASTRO = {
  email: cadastroEmail,
  senha: cadastroSenha,
  telefone: campoTelefone,
  cep: cadastroCep,
  logradouro: cadastroRua,
  numero: cadastroNumero,
  complemento: cadastroComplemento,
  bairro: cadastroBairro,
  cidade: cadastroCidade,
  consentimento: cadastroConsentimento,
}

// ---------- Cadastro em 3 etapas: Conta, Endereço, Confirmar ----------

const etapas = [...cadastroForm.querySelectorAll('.etapa')]
// Título e barra ficam em cima de todas as etapas; o título muda com a etapa aberta
const topoEtapas = document.querySelector('#etapas-topo')
const tituloEtapa = document.querySelector('#etapa-titulo')
const itensEtapa = [...topoEtapas.querySelectorAll('.etapas-item')]
const botaoVoltar = document.querySelector('#cadastro-voltar')
const botaoSeguir = document.querySelector('#cadastro-seguir')
const erroGeral = document.querySelector('#cadastro-geral-error')
const blocoPronto = document.querySelector('#cadastro-pronto')
const CURVA_SAIDA = 'cubic-bezier(.16, 1, .3, 1)'
let etapaAtual = 0
let trocandoEtapa = false
let enviandoCadastro = false

// "Continuar" confere só as regras da etapa aberta
const REGRAS_ETAPAS = [
  [
    [cadastroEmail, validarEmail],
    [cadastroSenha, validarSenhaCadastro],
    [campoTelefone, validarTelefone],
  ],
  [
    [cadastroCep, validarCep],
    [cadastroRua, validarTexto('a rua')],
    [cadastroNumero, validarNumero],
    [cadastroBairro, validarTexto('o bairro')],
    [cadastroCidade, validarTexto('a cidade')],
  ],
  [[cadastroConsentimento, validarConsentimento]],
]

function validarRegras(regras) {
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

  primeiroInvalido?.focus()
  return !primeiroInvalido
}

function etapaDoCampo(campo) {
  return Math.max(0, etapas.findIndex((etapa) => etapa.contains(campo)))
}

function atualizarBarra() {
  itensEtapa.forEach((item, i) => {
    item.classList.toggle('feita', i < etapaAtual)
    if (i === etapaAtual) item.setAttribute('aria-current', 'step')
    else item.removeAttribute('aria-current')
    dizer(item.querySelector('.etapas-estado'), i < etapaAtual ? ' (feita)' : '')
  })

  dizer(tituloEtapa, etapas[etapaAtual].dataset.titulo)
  botaoVoltar.hidden = etapaAtual === 0
  dizer(botaoSeguir.querySelector('.btn-label'), etapaAtual === etapas.length - 1 ? 'Criar conta' : 'Continuar')
}

function preencherResumo() {
  const numero = cadastroSemNumero.checked ? 'sem número' : cadastroNumero.value.trim()
  const complemento = cadastroComplemento.value.trim()
  const valores = {
    email: cadastroEmail.value.trim(),
    telefone: campoTelefone.value,
    rua: `${cadastroRua.value.trim()}, ${numero}${complemento ? `, ${complemento}` : ''}`,
    bairro: `${cadastroBairro.value.trim()}, ${cadastroCidade.value.trim()}`,
    cep: cadastroCep.value,
  }

  // textContent: é o que a pessoa digitou (e o que veio do ViaCEP)
  document.querySelectorAll('[data-resumo]').forEach((dd) => {
    dd.textContent = valores[dd.dataset.resumo]
  })
}

// Troca de etapa: a velha sai para o lado contrário e a nova entra na direção certa
// (para frente vem da direita, para trás vem da esquerda). O foco vai para o título novo
async function irParaEtapa(nova) {
  if (nova === etapaAtual || trocandoEtapa) return
  trocandoEtapa = true

  const antiga = etapas[etapaAtual]
  const proxima = etapas[nova]
  const sentido = nova > etapaAtual ? 1 : -1
  const animar = !Movimento.reduzido()

  if (animar) {
    await antiga
      .animate([{ opacity: 1 }, { opacity: 0, transform: `translateX(${sentido * -24}px)` }], {
        duration: 160,
        easing: 'cubic-bezier(.7, 0, .84, 0)',
      })
      .finished.catch(() => {})
  }

  etapaAtual = nova
  if (nova === etapas.length - 1) preencherResumo()
  antiga.hidden = true
  proxima.hidden = false
  atualizarBarra()

  if (animar) {
    // O título vem um pouco à frente dos campos
    ;[tituloEtapa, proxima].forEach((elemento, i) => {
      elemento.animate(
        [
          { opacity: 0, transform: `translateX(${sentido * 40}px)` },
          { opacity: 1, transform: 'none' },
        ],
        { duration: 420, delay: i * 60, easing: CURVA_SAIDA, fill: 'backwards' },
      )
    })
  }

  tituloEtapa.focus({ preventScroll: true })
  // No celular a etapa nova pode começar acima da tela: sobe até o título da etapa
  const topo = topoEtapas.getBoundingClientRect().top
  if (topo < 0) window.scrollBy({ top: topo - 16, behavior: animar ? 'smooth' : 'auto' })

  trocandoEtapa = false
}

botaoVoltar.addEventListener('click', () => irParaEtapa(etapaAtual - 1))

document.querySelectorAll('[data-ir-etapa]').forEach((botao) => {
  botao.addEventListener('click', () => irParaEtapa(Number(botao.dataset.irEtapa)))
})

// ---------- Senha: medidor de força ----------

const medidorForca = document.querySelector('#forca')
const dicaSenha = document.querySelector('#cadastro-password-hint')

cadastroSenha.addEventListener('input', () => {
  const { nivel, texto } = avaliarSenha(cadastroSenha.value)
  medidorForca.dataset.nivel = nivel
  dizer(dicaSenha, texto)
})

// ---------- CEP: busca a rua, o bairro e a cidade ----------

const caixaCep = cadastroCep.closest('.caixa')
const dicaCep = document.querySelector('#cadastro-cep-hint')
const DICA_CEP = dicaCep.textContent
let buscaCep = 0

// O campo que o CEP preencheu pisca de leve, para a pessoa ver o que mudou
function piscar(campo) {
  const caixa = campo.closest('.caixa')
  caixa.classList.remove('preenchido')
  void caixa.offsetWidth // reinicia a animação se piscar duas vezes seguidas
  caixa.classList.add('preenchido')
  caixa.addEventListener('animationend', () => caixa.classList.remove('preenchido'), { once: true })
}

// Máscara e, com os 8 dígitos, preenche o resto (dá para corrigir à mão)
cadastroCep.addEventListener('input', async () => {
  cadastroCep.value = formatarCep(cadastroCep.value)
  const minhaBusca = ++buscaCep
  caixaCep.classList.remove('buscando')

  if (cadastroCep.value.length !== 9) {
    dizer(dicaCep, DICA_CEP)
    return
  }

  caixaCep.classList.add('buscando')
  dizer(dicaCep, 'Buscando o endereço deste CEP…')

  const achado = await buscarCep(cadastroCep.value)
  if (minhaBusca !== buscaCep) return // a pessoa já mudou o CEP enquanto buscava
  caixaCep.classList.remove('buscando')

  if (!achado) {
    dizer(dicaCep, DICA_CEP)
    mostrarErro(cadastroCep, 'Não achamos esse CEP. Confira ou preencha o endereço abaixo.')
    return
  }

  dizer(dicaCep, 'Achamos o endereço. Confira e coloque o número.')
  ;[
    [cadastroRua, achado.logradouro],
    [cadastroBairro, achado.bairro],
    [cadastroCidade, achado.cidade],
  ].forEach(([campo, valor]) => {
    if (!valor) return // CEP de cidade inteira não tem rua: fica o que a pessoa digitou
    campo.value = valor
    limparErro(campo)
    piscar(campo)
  })

  trocarManchete(manchetePara('cadastro'))
  if (!cadastroSemNumero.checked) cadastroNumero.focus()
})

// A rua digitada à mão também vira a manchete
cadastroRua.addEventListener('change', () => trocarManchete(manchetePara('cadastro')))

cadastroSemNumero.addEventListener('change', () => {
  cadastroNumero.disabled = cadastroSemNumero.checked
  if (cadastroSemNumero.checked) {
    cadastroNumero.value = ''
    limparErro(cadastroNumero)
  }
})

// ---------- Envio ----------

function mostrarErroGeral(mensagem) {
  erroGeral.textContent = mensagem
  erroGeral.hidden = false
  Movimento.tremer(erroGeral)
}

function prenderBotao(preso) {
  botaoSeguir.disabled = preso
  botaoSeguir.classList.toggle('carregando', preso)
  const rotulo = botaoSeguir.querySelector('.btn-label')
  rotulo.textContent = preso ? `${botaoSeguir.dataset.carregando}…` : 'Criar conta'
}

function voltarAoComeco() {
  etapas.forEach((etapa, i) => {
    etapa.hidden = i !== 0
  })
  etapaAtual = 0
  atualizarBarra()
}

// Conta criada: estado de sucesso na própria tela, no lugar do formulário
function mostrarPronto(localizado) {
  const rua = cadastroRua.value.trim()
  loginEmail.value = cadastroEmail.value.trim() // o login já abre com o e-mail certo

  cadastroForm.reset()
  cadastroNumero.disabled = false
  medidorForca.dataset.nivel = 0
  dizer(dicaSenha, avaliarSenha('').texto)
  dizer(dicaCep, DICA_CEP)
  voltarAoComeco()

  cadastroForm.hidden = true
  topoEtapas.hidden = true
  blocoPronto.hidden = false
  document.querySelector('#pronto-mapa').hidden = localizado !== false

  trocarManchete(rua || 'Conta criada', 'Quando a chuva apertar na sua rua, o aviso chega no seu WhatsApp.')
  Movimento.aviso('Conta criada. Agora é só entrar.', { tipo: 'ok' })
  Movimento.vibrar(20)
  document.querySelector('#pronto-titulo').focus()
}

// Voltar ao #cadastro depois de criar a conta abre um formulário novo
function recomecarCadastro() {
  blocoPronto.hidden = true
  cadastroForm.hidden = false
  topoEtapas.hidden = false
  voltarAoComeco()
}

async function criarConta() {
  try {
    const resposta = await enviar('/auth/cadastro/', {
      email: cadastroEmail.value.trim(),
      senha: cadastroSenha.value,
      telefone: campoTelefone.value,
      cep: cadastroCep.value.replace(/\D/g, ''),
      logradouro: cadastroRua.value.trim(),
      numero: cadastroSemNumero.checked ? 'S/N' : cadastroNumero.value.trim(),
      complemento: cadastroComplemento.value.trim(),
      bairro: cadastroBairro.value.trim(),
      cidade: cadastroCidade.value.trim(),
      consentimento: cadastroConsentimento.checked,
    })

    if (resposta.ok) {
      const { localizado } = await resposta.json()
      mostrarPronto(localizado)
      return
    }

    if (resposta.status === 400) {
      const erros = await resposta.json()
      const campos = Object.keys(CAMPOS_CADASTRO).filter((nome) => erros[nome])

      // Volta para a etapa do primeiro campo errado e mostra cada erro no seu campo
      if (campos.length) {
        const primeiro = CAMPOS_CADASTRO[campos[0]]
        await irParaEtapa(etapaDoCampo(primeiro))
        campos.forEach((nome) => mostrarErro(CAMPOS_CADASTRO[nome], [].concat(erros[nome])[0]))
        primeiro.focus()
        return
      }

      mostrarErroGeral('Não deu para criar a conta. Confira os dados e tente de novo.')
      return
    }

    mostrarErroGeral(resposta.status === 429 ? ERRO_TENTATIVAS : ERRO_CONEXAO)
  } catch {
    mostrarErroGeral(ERRO_CONEXAO)
  }
}

// Enter num campo também chega aqui: avança a etapa ou, na última, cria a conta
cadastroForm.addEventListener('submit', async (evento) => {
  evento.preventDefault()
  if (trocandoEtapa || enviandoCadastro) return

  erroGeral.hidden = true
  if (!validarRegras(REGRAS_ETAPAS[etapaAtual])) return

  if (etapaAtual < etapas.length - 1) {
    irParaEtapa(etapaAtual + 1)
    return
  }

  enviandoCadastro = true
  prenderBotao(true)
  await criarConta()
  enviandoCadastro = false
  prenderBotao(false)
  atualizarBarra() // um erro do servidor pode ter levado de volta a outra etapa
})

window.addEventListener('hashchange', mostrarTela)
mostrarTela()

// Modo teste: só aparece neste computador (ver api.js) e não fala com o servidor
const blocoTeste = document.querySelector('#modo-teste')

if (MODO_TESTE_DISPONIVEL && blocoTeste) {
  blocoTeste.hidden = false

  blocoTeste.querySelectorAll('[data-teste]').forEach((botao) => {
    botao.addEventListener('click', () => {
      const papel = botao.dataset.teste
      limparSessao() // uma sessão de verdade guardada na aba passaria na frente do teste
      localStorage.setItem('token', 'modo-teste')
      localStorage.setItem('papel', papel)
      localStorage.setItem('modoTeste', '1')
      window.location.href = DESTINOS[papel]
    })
  })
}
