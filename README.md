# Citizen Assist AI

**Assistente digital de orientação cidadã** — Global Solution 2026.2 · Desafio CitizenTech · FIAP — Graduação ON em Ciência da Computação

🎥 **Vídeo de apresentação:** https://youtu.be/Lg2RSWOkn50

---

## Equipe

Trabalho individual.

| Nome | RM |
|---|---|
| Vitor Kubica Silveira | 573465 |

---

## 1. Problema, público e temas

Quem procura orientação sobre documentos, serviços públicos ou situações do dia a dia costuma encontrar informações espalhadas em vários sites, termos difíceis e instruções incompletas. A busca fica lenta e confusa, e o risco de seguir uma orientação errada aumenta.

O **Citizen Assist AI** é um protótipo de assistente em modo texto. Ele reúne orientações **verificadas em fontes oficiais**, responde em linguagem simples, **sempre cita a fonte** e **avisa quando não tem base suficiente** para orientar. O assistente é **não oficial**: não representa nenhum órgão, não faz atendimentos e não pede dados pessoais.

**Público beneficiado:** cidadãos que precisam de um primeiro caminho confiável para resolver demandas comuns. Isso inclui principalmente quem tem pouca familiaridade com portais públicos, como pessoas idosas, quem está procurando um serviço pela primeira vez e famílias em situação de vulnerabilidade.

**Temas abordados** (20 orientações):

| Tema | Subtemas | Exemplos |
|---|---|---|
| **Documentos** (7) | Acesso digital, Identificação, Registro civil, Cidadania, Trabalho | CPF, Carteira de Identidade Nacional, conta gov.br, 2ª via de certidão, título de eleitor, CTPS Digital |
| **Serviços** (7) | Saúde, Assistência social, Previdência e trabalho, Direitos do consumidor | Cartão SUS, Meu SUS Digital, Cadastro Único, Meu INSS, seguro-desemprego, consumidor.gov.br, direito de arrependimento |
| **Orientações comunitárias** (6) | Emergências, Proteção e direitos humanos, Assistência social | 190/192/193/199, o que informar na ligação, Disque 100, Ligue 180, CRAS, enchentes |

---

## 2. Como executar

O projeto exige **Python 3.9 ou superior** e usa só a biblioteca padrão. Não é preciso instalar nada.

```bash
python src/sistema.py
```

Outros comandos:

```bash
python src/sistema.py --validar      # valida a base (campos, IDs, relacionados) e o grafo
python src/sistema.py --mapa         # mostra a árvore Temas > Subtemas > Orientações
python src/sistema.py --modelo A     # inicia com o Modelo A de resposta
python src/avaliacao.py              # roda as 25 perguntas de teste e gera os indicadores
python src/usabilidade.py            # executa o roteiro de tarefas de usabilidade
python -m unittest discover tests -v # 25 testes unitários
```

> No macOS e no Linux, use `python3` caso o comando `python` não exista.

---

## 3. Estrutura do repositório

```text
citizen-assist-ai/
├── README.md
├── data/
│   ├── base_conhecimento.json   # 20 orientações verificadas (3 temas)
│   ├── perguntas_teste.json     # 25 perguntas de teste com resposta esperada
│   └── resultados_testes.csv    # registro gerado: esperado × obtido × acerto × tempo
├── docs/
│   ├── link_video.txt
│   ├── fontes.md                # fonte conferida de cada orientação
│   ├── estrategia_busca.md      # estruturas, grafo, algoritmo e calibração
│   ├── prompts.md               # modelos de instrução A e B e comparação
│   ├── resultados.md            # indicadores gerados pela avaliação
│   ├── teste_usabilidade.md     # roteiro de tarefas, dificuldades e melhorias
│   └── uso_ia.md                # uso de IA e validação crítica
├── notebooks/
├── src/
│   ├── sistema.py               # interface textual (ponto de entrada)
│   ├── base.py                  # leitura, validação e índices da base
│   ├── texto.py                 # normalização, sinônimos, dados pessoais
│   ├── busca.py                 # pontuação e decisão (resposta/ambígua/sem base)
│   ├── grafo.py                 # hierarquia de temas e grafo de relacionados
│   ├── respostas.py             # modelos de instrução A e B e mensagens
│   ├── avaliacao.py             # testes, taxa de acerto e tempo de consulta
│   └── usabilidade.py           # roteiro de tarefas automatizado
└── tests/
    └── test_sistema.py
```

---

## 4. Base de conhecimento

A base fica em `data/base_conhecimento.json`. Cada orientação é um objeto com os campos abaixo, **todos obrigatórios**:

| Campo | Conteúdo |
|---|---|
| `id` | Identificador único (`DOC-01`, `SER-03`, `COM-05`…) |
| `tema` | Chave do tema (`documentos`, `servicos`, `comunitarias`) |
| `subtema` | Agrupamento dentro do tema |
| `pergunta` | Pergunta que a orientação responde |
| `palavras_chave` | Lista de termos e expressões usados na busca |
| `orientacao` | Orientação resumida, em linguagem simples |
| `referencia` | `titulo` e `url` (https) da fonte consultada |
| `data_verificacao` | Data em que a fonte foi conferida (AAAA-MM-DD) |
| `aviso` | O que o cidadão deve confirmar antes de agir |
| `relacionados` | IDs de assuntos ligados (grafo de navegação) |

**Origem das orientações.** Todas foram conferidas em **18/11/2026** nas páginas oficiais: gov.br (Receita Federal, Governo Digital, Ministério da Saúde, MDS, INSS, Ministério do Trabalho, Ministério das Comunicações, MDHC, Ministério das Mulheres), Planalto (Código de Defesa do Consumidor), TSE, consumidor.gov.br, Registro Civil e Prefeitura de São Paulo. A tabela com a fonte de cada registro e os critérios de seleção está em [`docs/fontes.md`](docs/fontes.md).

**Validação e manutenção** (`src/base.py`):

- Arquivo **ausente**, **vazio** ou com **JSON inválido**: o programa encerra com uma mensagem clara, sem traceback.
- **Registro inconsistente** (campo faltando, tipo errado, tema desconhecido, URL sem https, data inválida, ID repetido): o registro é descartado e o problema é listado. Relacionados que apontam para IDs inexistentes são ignorados.
- **Acrescentar ou corrigir** uma orientação exige só editar o JSON. Depois, rode `python src/sistema.py --validar`.

---

## 5. Estruturas de dados, busca e navegação

Detalhes completos em [`docs/estrategia_busca.md`](docs/estrategia_busca.md).

| Estrutura | Uso |
|---|---|
| Lista de dicionários | Registros da base |
| Dicionário `id → registro` | Recuperação por identificador |
| Dicionário `tema → subtema → [ids]` | Hierarquia (árvore) usada no menu |
| Índice invertido `palavra → {ids}` | Recuperação por palavra-chave |
| Lista de adjacência | Grafo não direcionado de assuntos relacionados |
| `deque` (fila) | Busca em largura (menor caminho entre assuntos) |

**Algoritmo de busca:**

1. Valida a entrada: barra texto vazio e dados pessoais.
2. Normaliza: minúsculas, sem acento, sem stopwords, plural reduzido, sinônimos ("RG" → identidade, "demitido" → demissão, "alagamento" → enchente).
3. Pré-seleciona candidatos pelo índice invertido.
4. Pontua cada candidato de 0 a 1:

   `score = 0,55 × cobertura das palavras-chave + 0,25 × similaridade (difflib) + 0,25 se uma expressão-chave aparece inteira`

5. Decide:

| Condição | Comportamento |
|---|---|
| score do 1º < 0,30 | **Sem base:** aviso de limite + temas sugeridos |
| 1º e 2º com diferença < 0,08 | **Ambígua:** lista as opções e o usuário escolhe |
| demais casos | **Resposta** com o 1º colocado; os outros aparecem como relacionados |

**Várias correspondências.** A ordem é por score decrescente, com desempate pelo ID. Se um candidato se destaca, ele é a resposta. Se há empate técnico, o assistente não escolhe sozinho e pede ao usuário. Exemplo: "cartão" devolve SER-01 = 0,602 e SER-02 = 0,599, então o assistente pergunta qual dos dois.

**Navegação.** O usuário pode seguir dois caminhos:

- pelo menu, em Tema > Subtema > Orientação;
- por pergunta livre.

Depois de cada resposta aparecem **3 assuntos relacionados** do grafo, que formam uma corrente de continuidade. O grafo é **conexo**, e todo assunto tem pelo menos 3 vizinhos (os testes automáticos verificam as duas coisas). Exemplo real do teste de usabilidade: Cartão SUS → Meu SUS Digital → Níveis da conta gov.br → Documentos antes de solicitar um serviço.

---

## 6. Regras de resposta, modelos de instrução e limitações

O protótipo não usa LLM externo. Os modelos de instrução são **prompts documentados e aplicados em código** (`src/respostas.py`), sempre sobre o texto do registro encontrado. Detalhes em [`docs/prompts.md`](docs/prompts.md).

| | Modelo A — Resposta direta | Modelo B — Estruturada e verificável (**padrão**) |
|---|---|---|
| Papel | Assistente que responde perguntas | Assistente de orientação cidadã **não oficial** |
| Formato | Parágrafo + link | Tema › Subtema, orientação, fonte (título, link, data), aviso, 3 relacionados |
| Regras | Usar o texto da base | Fonte obrigatória; não inventar prazos, valores ou etapas; não alegar atendimento oficial; não pedir dados pessoais; informar limites; listar opções em ambiguidade |

**Comparação** nas mesmas perguntas de teste (critérios verificados automaticamente por `src/avaliacao.py`):

| Critério | A | B |
|---|---|---|
| Cita o link da fonte | 100% | 100% |
| Mostra data de verificação e aviso | 0% | 100% |
| Oferece continuidade (relacionados) | 0% | 100% |
| Explica o limite e declara que não vai inventar | 0% | 100% |
| **Média dos 10 critérios** | **10%** | **100%** |
| Tamanho médio do texto | 55 palavras | 129 palavras |

**Escolha: Modelo B.** Os dois usam o mesmo conteúdo, mas só o B mostra de quando é a informação, o que confirmar e como continuar. Os rótulos fixos tornam todas as respostas consistentes. O custo é um texto mais longo, compensado pela organização em blocos. O Modelo A continua disponível pela opção `[M]` do menu.

**Tratamento de limitações:**

| Situação | Comportamento |
|---|---|
| Entrada vazia | "Você não digitou nada. Escreva uma pergunta ou escolha uma opção do menu." |
| Opção inexistente | `Opção "9" não existe. Digite um dos números ou letras mostrados entre colchetes.` |
| Pergunta fora da base | Aviso de limite, compromisso de não inventar, temas sugeridos e indicação do canal oficial |
| Consulta ambígua | Lista numerada de opções para escolher |
| Dados pessoais (CPF, e-mail, telefone) | Mensagem descartada sem busca e sem registro, com orientação para reescrever |
| Base ausente, vazia ou inconsistente | Mensagem clara na inicialização, ou registro descartado com aviso |
| Ctrl+C / fim da entrada | Encerramento sem erro, com mensagem de despedida |

---

## 7. Exemplos de uso

**Pergunta do vídeo** (`Quais documentos consultar antes de solicitar um serviço?`):

```text
Documentos › Acesso digital  [DOC-01]

Antes de pedir um serviço público, separe o número do CPF e confira se você
tem uma conta gov.br, pois muitos serviços digitais pedem os dois. O CPF é
obrigatório para criar a conta gov.br, e o cadastro também pede e-mail ou
celular para validação. Tenha à mão um documento de identificação com foto
(CIN, CNH ou passaporte). Na página de cada serviço, confira a lista exata de
documentos e o nível de conta exigido.

Fonte consultada: Conta gov.br — Dúvidas frequentes: cadastro sem CPF
  https://acesso.gov.br/faq/_perguntasdafaq/cadastrosemcpf.html
  Verificado em 18/11/2026

⚠ Aviso: Cada serviço tem requisitos próprios. Confirme a lista atualizada na
página oficial do serviço antes de sair de casa.

Assuntos relacionados para continuar:
  [1] Como faço a inscrição no CPF?
  [2] Quais são os níveis da conta gov.br e como aumentar o nível?
  [3] O que é a Carteira de Identidade Nacional (CIN) e quanto custa a primeira via?
```

**Pergunta fora da base** (`Como funciona um foguete?`):

```text
Não encontrei na base verificada uma orientação confiável para essa pergunta.
Para não correr o risco de passar uma informação errada, não vou inventar uma
resposta.

Você pode tentar:
  • reformular a pergunta com outras palavras (ex.: "como tirar o CPF");
  • navegar pelos temas disponíveis:
      - Documentos: Acesso digital, Identificação, Registro civil, Cidadania, Trabalho
      - Serviços: Saúde, Assistência social, Previdência e trabalho, Direitos do consumidor
      - Orientações comunitárias: Emergências, Proteção e direitos humanos, Assistência social
  • procurar o canal oficial do órgão responsável pelo assunto.
```

**Consulta ambígua** (`documento`):

```text
Sua pergunta pode se referir a assuntos diferentes. Qual deles você procura?
  [1] Quais documentos consultar antes de solicitar um serviço?
  [2] O que é a Carteira de Identidade Nacional (CIN) e quanto custa a primeira via?
```

**Entradas inválidas no menu:**

```text
Escolha uma opção ou digite sua pergunta:            ← Enter sem texto
Você não digitou nada. Escreva uma pergunta ou escolha uma opção do menu.
Escolha uma opção ou digite sua pergunta: 9
Opção "9" não existe. Digite um dos números ou letras mostrados entre colchetes.
Escolha uma opção ou digite sua pergunta: meu cpf é 123.456.789-09
Parece que a mensagem contém dados pessoais (CPF, telefone ou e-mail). Por
segurança ela foi descartada e não foi registrada. ...
```

---

## 8. Plano de testes, indicadores e interpretação

**Plano.** As 25 perguntas de `data/perguntas_teste.json` têm resposta esperada definida antes da execução:

| Categoria | Qtd. | Exemplo |
|---|---|---|
| Dúvidas diretas | 5 | "Como faço para tirar o CPF?" |
| Reformulações | 13 | "Fui mandado embora sem justa causa, tenho direito a algum benefício?" |
| Fora do tema | 2 | "Como funciona um foguete?" |
| Sem resposta confiável | 1 | "Qual o valor do aluguel social em Curitiba?" |
| Limitações | 4 | entrada vazia, consulta ambígua ("documento"), dados pessoais, opção inexistente ("9") |

`python src/avaliacao.py` registra em [`data/resultados_testes.csv`](data/resultados_testes.csv), para cada pergunta:

- a orientação esperada e a resposta obtida;
- o score e a classificação **acerto/erro**;
- o tempo de consulta (média de 20 medições com `time.perf_counter`).

### Resultados obtidos

Os valores abaixo são da execução registrada em [`docs/resultados.md`](docs/resultados.md):

| Indicador | Resultado |
|---|---|
| Perguntas testadas | 25 |
| Acertos | 24 |
| **Taxa de acerto** (acertos ÷ total × 100) | **96,0%** |
| Acerto em dúvidas diretas | 100% (5/5) |
| Acerto em reformulações | 92,3% (12/13) |
| Acerto em fora do tema / sem resposta confiável / limitações | 100% (7/7) |
| **Tempo médio de consulta** | **0,71 ms** (maior: 1,43 ms) |
| **Facilidade de uso** (roteiro de 6 tarefas) | 6/6 concluídas; 25 interações contra 22 ideais (88% de eficiência) |

> O vídeo cita 83,3% (10 acertos em 12) como **exemplo do enunciado**. A taxa medida no protótipo é a desta tabela. Os tempos variam alguns centésimos de milissegundo a cada execução.

### Interpretação

- **O que funciona bem.** Perguntas diretas, reformulações com vocabulário próximo da base e todos os casos-limite tiveram comportamento correto. O assistente **nunca respondeu com segurança uma pergunta fora da base**: os 3 casos fora do tema ou sem resposta confiável viraram aviso de limite. Para orientação cidadã, esse é o erro mais grave a evitar.
- **O erro observado (T16).** A pergunta "Dá para mostrar o cartão do SUS pelo celular?" devolveu o Cartão SUS (SER-01, score 0,645) em vez do Meu SUS Digital (SER-02, 0,554). O motivo é que a busca é **lexical**: "cartão do SUS" casa forte com SER-01, e a intenção "no celular" depende de vocabulário que a base não cobre bem ("mostrar" contra "apresentar"). Mesmo assim, o SER-02 aparece como 1º assunto relacionado, a um passo do usuário.
- **Tempo.** Menos de 2 ms por consulta. O tempo não é gargalo para uma base deste tamanho, e o índice invertido mantém a busca rápida quando a base crescer.
- **Usabilidade.** As maiores perdas vieram de digitar o nome do assunto em vez do número (U2) e de não poder escolher um tema direto na tela de limite (U4). O roteiro também revelou um defeito de navegação: o assistente oferecia de volta o assunto anterior. Esse defeito **foi corrigido** (ver [`docs/teste_usabilidade.md`](docs/teste_usabilidade.md)).

### Limitações da avaliação

- 25 perguntas é uma amostra pequena, escrita pelo próprio autor, que conhece o vocabulário da base. A taxa real com cidadãos tende a ser menor, sobretudo em reformulações.
- O limiar (0,30) e a margem (0,08) foram calibrados com essas mesmas perguntas. Um conjunto de validação separado daria uma medida menos otimista.
- O teste de usabilidade foi um roteiro de tarefas conduzido pelo autor, não uma sessão com usuários externos. O tempo medido é de processamento, não de leitura e decisão humana.
- A classificação acerto/erro considera o registro retornado, não a qualidade da redação, que foi avaliada à parte na comparação dos modelos.

---

## 9. Clareza, acessibilidade, privacidade e informação não oficial

- **Clareza.** As orientações são resumidas em frases curtas, sem jargão, e as siglas são explicadas (CIN, CRAS, PAIF). As respostas seguem sempre o mesmo formato, com rótulos fixos.
- **Acessibilidade.** A interface é só texto: funciona em qualquer terminal e com leitores de tela, e não depende de cores. As linhas têm até 78 colunas. A navegação usa números curtos, e qualquer erro de digitação gera uma explicação em vez de travar o programa. A pergunta livre é aceita direto no menu, sem passos extras.
- **Privacidade.** O assistente **não pede** nenhum dado pessoal e avisa isso na abertura. Mensagens com padrão de CPF, e-mail ou telefone são descartadas. **Nada do que o usuário digita é gravado**: o histórico da sessão guarda só os IDs das orientações exibidas, em memória.
- **Informação não oficial.** O cabeçalho diz "assistente não oficial". O sistema não promete integração com órgãos públicos e não aciona serviços. Toda resposta traz fonte, data de verificação e aviso para confirmar no canal oficial. Nas orientações de emergência, o aviso lembra que o assistente não aciona nenhum serviço.

---

## 10. Uso de IA

O protótipo **não usa** modelo de linguagem externo: toda resposta é um trecho de um registro da base verificada. Cada informação foi conferida pelo autor na página oficial da fonte, e foram descartadas as que a fonte não confirmava. Detalhes em [`docs/uso_ia.md`](docs/uso_ia.md).

---

## 11. Conclusões, limitações e melhorias

**Conclusões.** O protótipo cumpre o fluxo completo do desafio:

- recebe a pergunta ou a escolha no menu e valida a entrada;
- busca na base verificada e responde com fonte, data e aviso;
- oferece a continuação por assuntos relacionados;
- quando não há base suficiente, diz isso claramente, sem inventar.

A taxa de acerto foi de 96,0% nas 25 perguntas de teste, com tempo médio abaixo de 1 ms.

**Limitações:**

- **Busca lexical.** O sistema depende das palavras-chave e de uma lista fixa de sinônimos. Reformulações com vocabulário muito diferente podem falhar (caso T16).
- **Base pequena** (20 orientações) e com abrangência nacional. Regras estaduais e municipais, como valores da 2ª via da CIN ou endereços do CRAS, ficaram fora de propósito e aparecem só como aviso.
- **Informação datada.** A data de verificação precisa ser renovada periodicamente. O sistema não detecta mudanças nas páginas oficiais.
- **Interface de terminal**, ainda não testada com usuários externos.

**Melhorias possíveis:**

1. **Busca semântica com validação.** Usar embeddings ou um LLM só para *interpretar* a pergunta e escolher o registro. A resposta continuaria sendo o texto da base, conferido pela URL da fonte. Isso resolveria casos como o T16 sem abrir espaço para respostas inventadas.
2. **Navegação mais tolerante.** Aceitar o nome do subtema além do número e numerar os temas sugeridos na tela de limite. As duas dificuldades apareceram no teste de usabilidade.
3. **Rotina de reverificação.** Criar um script que verifique se as URLs da base continuam no ar e marque registros com mais de 6 meses desde a última verificação.
4. **Teste com usuários reais** e conjunto de validação separado para calibrar o limiar.
5. **Mais canais:** versão web ou chatbot, mantendo as mesmas regras de fonte, aviso e privacidade.

---

## Vídeo

https://youtu.be/Lg2RSWOkn50
