// CEP: máscara e busca da rua, do bairro e da cidade no ViaCEP.
// Só o CEP sai do computador; o número da casa fica só com a ALERA.

function formatarCep(valor) {
  const digitos = valor.replace(/\D/g, '').slice(0, 8)
  return digitos.length > 5 ? `${digitos.slice(0, 5)}-${digitos.slice(5)}` : digitos
}

// Devolve { logradouro, bairro, cidade } ou null se o CEP não existir ou o serviço falhar
async function buscarCep(cep) {
  const digitos = cep.replace(/\D/g, '')
  if (digitos.length !== 8) return null

  try {
    const resposta = await fetch(`https://viacep.com.br/ws/${digitos}/json/`)
    if (!resposta.ok) return null

    const dados = await resposta.json()
    if (dados.erro) return null

    return {
      logradouro: dados.logradouro || '',
      bairro: dados.bairro || '',
      cidade: dados.localidade || '',
    }
  } catch {
    return null
  }
}
