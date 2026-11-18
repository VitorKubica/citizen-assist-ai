# Resultados dos testes

> Arquivo gerado automaticamente por `python src/avaliacao.py`. O registro detalhado está em `data/resultados_testes.csv`.

## Indicadores

| Indicador | Valor |
|---|---|
| Perguntas de teste | 25 |
| Classificadas como acerto | 24 |
| **Taxa de acerto** | **96,0%** (24/25) |
| Tempo médio de consulta | 0.71 ms |
| Maior tempo de consulta | 1.43 ms |

Fórmulas: taxa de acerto = acertos ÷ total × 100; tempo médio = média dos tempos medidos.
Cada consulta foi repetida 20 vezes com `time.perf_counter()` (busca + formatação da resposta) e registrou-se a média; a opção de menu foi medida em uma execução da sessão completa.

### Acerto por categoria

| Categoria | Acertos | Total | Taxa |
|---|---|---|---|
| direta | 5 | 5 | 100,0% |
| reformulacao | 12 | 13 | 92,3% |
| fora_do_tema | 2 | 2 | 100,0% |
| sem_resposta_confiavel | 1 | 1 | 100,0% |
| limitações | 4 | 4 | 100,0% |

## Registro dos testes

| ID | Categoria | Entrada | Esperado | Obtido | Resultado | Tempo (ms) |
|---|---|---|---|---|---|---|
| T01 | direta | Quais documentos consultar antes de solicitar um serviço? | DOC-01 | DOC-01 | acerto | 0.896 |
| T02 | direta | Como faço para tirar o CPF? | DOC-02 | DOC-02 | acerto | 0.888 |
| T03 | reformulacao | Não tenho CPF, onde consigo me inscrever? | DOC-02 | DOC-02 | acerto | 0.926 |
| T04 | direta | A primeira via da carteira de identidade nacional é paga? | DOC-03 | DOC-03 | acerto | 1.262 |
| T05 | reformulacao | como tirar o novo RG | DOC-03 | DOC-03 | acerto | 0.846 |
| T06 | direta | Como aumentar o nível da minha conta gov.br para ouro? | DOC-04 | DOC-04 | acerto | 1.057 |
| T07 | reformulacao | Perdi minha certidão de nascimento, como peço outra? | DOC-05 | DOC-05 | acerto | 0.584 |
| T08 | reformulacao | Fui mandado embora sem justa causa, tenho direito a algum benefício? | SER-05 | SER-05 | acerto | 1.425 |
| T09 | reformulacao | Comprei pela internet e me arrependi, posso devolver? | SER-07 | SER-07 | acerto | 0.776 |
| T10 | direta | Qual número ligar em caso de enchente? | COM-06 | COM-06 | acerto | 1.048 |
| T11 | reformulacao | Onde denunciar violência contra idoso? | COM-03 | COM-03 | acerto | 0.964 |
| T12 | reformulacao | Como me cadastrar no Bolsa Família? | SER-03 | SER-03 | acerto | 0.743 |
| T13 | reformulacao | meu marido me bateu, onde peço ajuda | COM-04 | COM-04 | acerto | 0.549 |
| T14 | reformulacao | Quero ver o extrato da minha aposentadoria | SER-04 | SER-04 | acerto | 0.564 |
| T15 | reformulacao | Qual o telefone do SAMU? | COM-01 | COM-01 | acerto | 0.522 |
| T16 | reformulacao | Dá para mostrar o cartão do SUS pelo celular? | SER-02 | SER-01 | erro | 0.762 |
| T17 | reformulacao | Preciso tirar a carteira de trabalho | DOC-07 | DOC-07 | acerto | 1.256 |
| T18 | reformulacao | A empresa não resolve meu problema, onde posso reclamar? | SER-06 | SER-06 | acerto | 0.559 |
| T19 | fora_do_tema | Como funciona um foguete? | sem_base | sem_base | acerto | 0.310 |
| T20 | fora_do_tema | Qual a previsão do tempo para amanhã? | sem_base | sem_base | acerto | 0.310 |
| T21 | sem_resposta_confiavel | Qual o valor do aluguel social em Curitiba? | sem_base | sem_base | acerto | 0.698 |
| T22 | limitacao_vazia | (vazia) | vazia | vazia | acerto | 0.001 |
| T23 | limitacao_ambigua | documento | ambigua | ambigua | acerto | 0.581 |
| T24 | limitacao_dados_pessoais | meu cpf é 123.456.789-09, está regular? | dados_pessoais | dados_pessoais | acerto | 0.001 |
| T25 | limitacao_opcao_inexistente | 9 | opcao_invalida | opcao_invalida | acerto | 0.123 |

## Comparação dos modelos de instrução (A × B)

Os dois modelos foram aplicados às mesmas respostas obtidas nos testes. Cada critério é verificado automaticamente no texto exibido ao usuário.

| Critério | Modelo A | Modelo B |
|---|---|---|
| Cita o link da fonte | 100% | 100% |
| Identifica a fonte pelo nome | 0% | 100% |
| Mostra a data de verificação | 0% | 100% |
| Traz aviso de confirmação | 0% | 100% |
| Indica tema e subtema | 0% | 100% |
| Oferece assuntos relacionados | 0% | 100% |
| Explica que não há base suficiente | 0% | 100% |
| Declara que não vai inventar | 0% | 100% |
| Sugere temas ou outra consulta | 0% | 100% |
| Remete ao canal oficial | 0% | 100% |
| **Média dos critérios** | **10%** | **100%** |
| Tamanho médio do texto exibido | 55 palavras | 129 palavras |

Os critérios vêm dos requisitos do desafio (citar a fonte, avisar quando confirmar, informar limites e oferecer continuidade). Como custo, o Modelo B exibe textos mais longos; para compensar, ele usa blocos curtos e rótulos fixos (Fonte, Aviso, Assuntos relacionados), que facilitam a leitura em tela.

**Escolha: Modelo B (padrão do sistema).** O Modelo A só entrega o texto e o link: o cidadão não sabe de quando é a informação, não recebe o aviso para confirmar requisitos e, quando não há base, recebe apenas "Não encontrei uma resposta", sem caminho para continuar. O Modelo B mantém a mesma orientação (não acrescenta conteúdo), mas sempre mostra fonte, data de verificação, aviso e próximos passos, o que torna as respostas mais claras e consistentes entre si.

## Erros observados

- **T16** — "Dá para mostrar o cartão do SUS pelo celular?": esperado `SER-02`, obtido `SER-01` (score 0.645).
