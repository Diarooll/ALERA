# ALERA

**Acompanhamento Local de Emergências e Riscos Ambientais.** No lugar certo, na hora certa.

O ALERA é um projeto de alerta de chuva com o nome da sua rua, entregue no WhatsApp. Ele cruza a previsão do tempo com as áreas de risco de Juiz de Fora (MG) e avisa o morador antes da água subir ou do barranco ceder.

> **Status:** protótipo de front-end. Este repositório tem o site e uma prévia navegável do app. O cadastro, o envio de alertas e os gadgets ainda não funcionam de verdade: o back-end e o banco de dados são os próximos passos.

## O problema

Fevereiro de 2026 foi o pior verão da história recente de Juiz de Fora:

- **65** mortes nas chuvas de fevereiro
- **8.854** pessoas desabrigadas ou desalojadas
- **128 mil** pessoas vivendo em áreas de risco
- **142** áreas de risco geológico mapeadas

O alerta que existe hoje vale para a cidade toda. Ele não diz qual rua ou qual encosta corre risco, e quando todo aviso parece igual, ninguém sai de casa.

As fontes desses números estão na seção de referências do site.

## Como funciona

### Fase 1: ALERA Web

Começa sem instalar nada, só com o celular:

1. **Cadastre sua rua:** o morador informa o telefone e a rua onde mora.
2. **Script + IA:** a ALERA cruza a previsão de chuva com as 142 áreas de risco da cidade.
3. **O alerta chega no WhatsApp:** com o nome da rua, o nível de risco, o que fazer e o abrigo mais próximo.

| Nível | O que significa |
| --- | --- |
| Normal | Sem risco na sua rua. Siga sua rotina. |
| Atenção | Chuva prevista para hoje. Confira seu abrigo e tire o lixo da frente do bueiro. |
| Alerta | Chuva forte em até 2 horas. Evite a rua e deixe documentos à mão. |
| Perigo | Risco agora. Saia de casa e vá para o abrigo. |

O app também tem missões que valem pontos, como plantar uma muda na encosta e salvar o abrigo mais próximo, e um ranking por rua. Os valores que aparecem no protótipo são simulados.

### Fase 2: Gadgets ALERA

Os gadgets entram aos poucos, área por área. O dado medido entra no mesmo alerta do WhatsApp, e os gadgets também notificam a Defesa Civil e a Secretaria de Obras.

- **Sensor ALERA:** fica na encosta e mede a umidade do solo, a chuva acumulada e a inclinação do terreno. Avisa com LEDs na rua, sirene e WhatsApp.
- **Bueiro ALERA:** um cesto segura o lixo antes da galeria, e o sensor avisa a Secretaria de Obras quando é hora de limpar.

## Como abrir

Não precisa instalar nada. Abra no navegador:

- `front-end/index.html`: site do projeto
- `front-end/app/login.html`: login do app

Como ainda não há back-end, criar uma conta não salva nada. Para entrar no app, use o usuário de demonstração:

- **E-mail:** `adminalera@alera.com.br`
- **Senha:** `adminAlera`



## Equipe

**MonkeyNerds** · FIAP · Challenge 2026

- Daniel Souza Gomes
- Victor Santos Ferreira de Morais
- Diego Ramos Pereira Gonzalez
- Diego Alejandro Ribeiro Olalla
