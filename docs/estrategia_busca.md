# Estratégia de busca e organização dos assuntos

## 1. Estruturas de dados

| Estrutura | Onde | Para quê |
|---|---|---|
| Lista de dicionários | `BaseConhecimento.registros` | Cada orientação é um dicionário com os campos do JSON |
| Dicionário `id → registro` | `BaseConhecimento.por_id` | Recuperação direta por identificador |
| Dicionário aninhado `tema → subtema → [ids]` | `BaseConhecimento.por_tema` | Hierarquia usada no menu (árvore) |
| Índice invertido `palavra → {ids}` | `BaseConhecimento.por_palavra` | Pré-seleção rápida de candidatos pela palavra-chave |
| Lista de adjacência `id → [ids vizinhos]` | `GrafoAssuntos.adjacencia` | Grafo de assuntos relacionados |
| Fila (`collections.deque`) | `GrafoAssuntos.caminho` | Busca em largura no grafo |

## 2. Hierarquia de temas (árvore)

São três temas, cada um com subtemas, e cada subtema com suas orientações. Para ver a árvore completa, rode `python src/sistema.py --mapa`.

```
Citizen Assist AI
├── Documentos
│   ├── Acesso digital ......... DOC-01, DOC-04
│   ├── Identificação .......... DOC-02, DOC-03
│   ├── Registro civil ......... DOC-05
│   ├── Cidadania .............. DOC-06
│   └── Trabalho ............... DOC-07
├── Serviços
│   ├── Saúde .................. SER-01, SER-02
│   ├── Assistência social ..... SER-03
│   ├── Previdência e trabalho . SER-04, SER-05
│   └── Direitos do consumidor . SER-06, SER-07
└── Orientações comunitárias
    ├── Emergências ............ COM-01, COM-02, COM-06
    ├── Proteção e direitos humanos . COM-03, COM-04
    └── Assistência social ..... COM-05
```

## 3. Grafo de assuntos relacionados

Cada orientação é um vértice. O campo `relacionados` de cada registro cria arestas **não direcionadas**. A ligação representa "quem procurou A costuma precisar de B logo depois". Exemplos de relações usadas:

- **Pré-requisito:** CPF (DOC-02) → conta gov.br (DOC-04) → Meu INSS (SER-04). Cada serviço exige o anterior.
- **Mesmo problema, outro canal:** Disque 100 (COM-03) ↔ Ligue 180 (COM-04) ↔ telefones de emergência (COM-01).
- **Porta de entrada:** CRAS (COM-05) ↔ Cadastro Único (SER-03).
- **Escalonamento:** reclamação no consumidor.gov.br (SER-06) ↔ direito de arrependimento (SER-07).

Propriedades verificadas pelos testes automáticos:

- O grafo é **conexo**: de qualquer assunto se chega a qualquer outro.
- Todo assunto tem **pelo menos 3 vizinhos**, então a tela sempre oferece 3 opções de continuidade.
- A navegação **não oferece de volta** o assunto de onde o usuário acabou de vir. Esse defeito foi encontrado no teste de usabilidade e corrigido.

## 4. Algoritmo de busca

Fluxo de `busca.buscar(base, consulta)`:

1. **Validação.** Entrada vazia vira `vazia`. Texto com padrão de CPF, e-mail ou telefone vira `dados_pessoais`, e a mensagem é descartada sem passar pela busca.
2. **Normalização** (`texto.tokenizar`):
   - minúsculas, sem acentos, sem pontuação;
   - remoção de *stopwords* ("como", "faço", "meu"…);
   - redução simples de plural ("documentos" → "documento");
   - troca de sinônimos por termos da base ("RG" → "identidade", "demitido" → "demissão", "alagamento" → "enchente").
3. **Pré-seleção.** Os candidatos são os registros que aparecem no índice invertido para algum termo da consulta, mais os que têm termo em comum com a pergunta cadastrada. Se não sobra nenhum candidato, a consulta vai direto para *sem base*.
4. **Pontuação de 0 a 1** de cada candidato:
   - `cobertura = (2 × termos nas palavras-chave + 1 × termos só na pergunta/subtema) ÷ (2 × termos da consulta)`
   - `frase = 0,25` se uma palavra-chave composta ("sem justa causa", "conta gov.br") aparece inteira na consulta
   - `similar = difflib.SequenceMatcher(consulta, pergunta cadastrada).ratio()`
   - `score = min(1; 0,55 × cobertura + 0,25 × similar + frase)`
5. **Decisão por regras** (condicionais em `buscar`):

| Situação | Condição | Resultado |
|---|---|---|
| Sem base suficiente | score do 1º < **0,30** (`LIMIAR`) | aviso de limite + temas sugeridos |
| Ambígua | 1º e 2º com diferença < **0,08** (`MARGEM_AMBIGUIDADE`) | lista de opções para o usuário escolher |
| Resposta | demais casos | orientação do 1º colocado |

### Comportamento com várias correspondências

- Os candidatos são ordenados por **score decrescente**. Em caso de empate exato, vale a ordem do **ID**, para o resultado ser determinístico.
- Quando um candidato se destaca, por exemplo "Como faço o cartão do SUS?" (SER-01 = 0,93 contra SER-02 = 0,67), o sistema responde com ele e mostra os demais nos **assuntos relacionados**.
- Quando há **empate técnico**, por exemplo "cartão" (SER-01 = 0,602 contra SER-02 = 0,599) ou "documento" (DOC-01 = 0,62 contra DOC-03 = 0,58), o sistema **não escolhe sozinho**: lista até 3 opções e pede para o usuário escolher.

### Por que esse método

- Usa só listas, dicionários, conjuntos e a biblioteca padrão. É explicável, determinístico e roda em menos de 2 ms por consulta.
- Pesar mais as palavras-chave favorece termos que a equipe curou para cada orientação. A similaridade de texto ajuda com reformulações próximas da pergunta cadastrada.
- O limiar transforma a "falta de confiança" em comportamento explícito (aviso de limite), em vez de devolver a orientação "menos pior".

### Calibração

O limiar 0,30 e a margem 0,08 foram ajustados com as perguntas de teste:

- as perguntas fora do tema ficaram abaixo de 0,23;
- as respostas corretas com menor score (reformulações como "meu marido me bateu, onde peço ajuda", 0,40) ficaram acima de 0,30.

Os valores são constantes no início de `src/busca.py` e podem ser recalibrados quando a base crescer.

## 5. Como acrescentar uma orientação

1. Acrescente o registro em `data/base_conhecimento.json`, com palavras-chave e até 3 relacionados.
2. Rode `python src/sistema.py --validar`. O comando confere os campos e se o grafo continua conexo.
3. Inclua uma pergunta em `data/perguntas_teste.json` e rode `python src/avaliacao.py` para ver o impacto na taxa de acerto.

Nenhuma linha de código precisa mudar.
