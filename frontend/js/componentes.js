// ALERA · componentes.js
// Só a linha "Experimente" da vitrine (app/componentes.html). Os estados hover, focus, active e
// disabled vêm direto do CSS; aqui só ficam os estados que dependem de uma ação (error e buscando).

const $ = (seletor) => document.querySelector(seletor)

// Botão: o clique simula uma falha. O botão vira "Tentar de novo" (error); o próximo clique conserta
const botaoVivo = $('#vivo-botao')
botaoVivo.addEventListener('click', () => {
  const comErro = botaoVivo.classList.toggle('botao--erro')
  botaoVivo.textContent = comErro ? 'Tentar de novo' : 'Salvar este abrigo'
  $('#vivo-botao-ajuda').textContent = comErro
    ? 'Erro: a ação falhou. Clique de novo para voltar ao default.'
    : 'Clique no primeiro botão: ele simula uma falha e passa para o estado de erro.'
})

// Campo de texto: vazio ao sair = erro embaixo do campo; digitar apaga
function erroNoCampo(entrada, caixa, texto) {
  if (texto) entrada.setAttribute('aria-invalid', 'true')
  else entrada.removeAttribute('aria-invalid')
  caixa.textContent = texto
  caixa.hidden = !texto
}

const campoVivo = $('#vivo-campo')
const campoVivoErro = $('#vivo-campo-erro')
campoVivo.addEventListener('blur', () => {
  if (!campoVivo.value.trim()) erroNoCampo(campoVivo, campoVivoErro, 'Informe o bairro.')
})
campoVivo.addEventListener('input', () => erroNoCampo(campoVivo, campoVivoErro, ''))

// Card: "Ver no mapa" liga e desliga o active; "Salvar" simula falha (error)
const cardVivo = $('#vivo-card')
$('#vivo-card-ver').addEventListener('click', () => cardVivo.classList.toggle('abrigo-cartao--ativo'))

const salvarVivo = $('#vivo-card-salvar')
salvarVivo.addEventListener('click', () => {
  const comErro = cardVivo.classList.toggle('abrigo-cartao--erro')
  salvarVivo.classList.toggle('botao--erro', comErro)
  salvarVivo.textContent = comErro ? 'Tentar de novo' : 'Salvar este abrigo'
  cardVivo.querySelector('.abrigo-cartao__erro').textContent = comErro
    ? 'Não foi possível salvar. Tente de novo.'
    : ''
})

// Composto: o mesmo comportamento do CEP em Meus dados (máscara, busca no ViaCEP, erro)
const cepVivo = $('#vivo-cep')
const cepAjuda = $('#vivo-cep-ajuda')
const cepErro = $('#vivo-cep-erro')

cepVivo.addEventListener('input', async () => {
  cepVivo.value = formatarCep(cepVivo.value)
  erroNoCampo(cepVivo, cepErro, '')
  if (cepVivo.value.length !== 9) {
    cepAjuda.textContent = ''
    cepVivo.removeAttribute('aria-busy')
    return
  }

  const cep = cepVivo.value
  cepAjuda.textContent = 'Buscando o endereço deste CEP…'
  cepVivo.setAttribute('aria-busy', 'true')
  const achado = await buscarCep(cep)
  if (cepVivo.value !== cep) return
  cepVivo.removeAttribute('aria-busy')

  if (!achado) {
    cepAjuda.textContent = ''
    erroNoCampo(cepVivo, cepErro, 'Não achamos este CEP. Confira os números.')
    return
  }
  cepAjuda.textContent = `${achado.logradouro || 'Rua não informada'} · ${achado.bairro} · ${achado.cidade}`
})
