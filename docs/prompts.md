# Modelos de instrução de resposta (prompts)

O Citizen Assist AI **não envia perguntas a um modelo de linguagem externo**. As respostas vêm sempre de um registro da base verificada. Os "prompts" do projeto são **instruções de resposta** que definem três coisas:

- **Papel:** quem o assistente é.
- **Formato:** como a resposta aparece.
- **Regras:** o que é obrigatório e o que é proibido.

Cada instrução é implementada em código, em `src/respostas.py`, por uma função que monta a resposta a partir do registro encontrado. Assim, a instrução documentada e o comportamento real são a mesma coisa. Também não existe risco de o texto exibido conter algo que não está na base.

O texto completo das duas instruções fica nas constantes `INSTRUCAO_A` e `INSTRUCAO_B` de `src/respostas.py`.

## Modelo A — Resposta direta

```
Papel: assistente que responde perguntas do cidadão.
Formato: um parágrafo com a orientação encontrada, seguido do link da fonte.
Regras: usar o texto da orientação da base.
```

**Exemplo** (pergunta: "Qual número ligar em caso de enchente?"):

```
Em desastres e situações de risco, como enchentes, deslizamentos e áreas de
risco, ligue para a Defesa Civil no número 199. Se houver pessoas feridas ou
presas, acione também o Corpo de Bombeiros (193) ou o SAMU (192).
Fonte: https://www.gov.br/mcom/pt-br/noticias/noticias_alt/2026/setembro/emergencia-voce-sabe-para-quem-ligar-quando-precisa-de-ajuda
```

Quando não há base, o Modelo A responde apenas `Não encontrei uma resposta.`

## Modelo B — Orientação estruturada e verificável (padrão)

```
Papel: você é o Citizen Assist AI, um assistente de orientação cidadã NÃO
oficial. Você organiza informações públicas verificadas; não representa nenhum
órgão e não realiza atendimentos.
Formato obrigatório:
  1. Tema › Subtema (para o cidadão saber onde está);
  2. Orientação em linguagem simples, usando só o texto do registro da base;
  3. Fonte: título, link e data de verificação;
  4. Aviso de confirmação do registro;
  5. Até 3 assuntos relacionados para continuar a consulta.
Regras:
  - citar a fonte é obrigatório; sem fonte, não responda;
  - não invente prazos, valores, documentos ou etapas que não estejam no registro;
  - nunca diga que o atendimento é oficial nem peça dados pessoais;
  - se não houver registro com confiança suficiente, informe o limite, diga que
    não vai inventar e sugira temas ou outra forma de perguntar;
  - se a pergunta for ambígua, liste as opções e peça para o cidadão escolher.
```

**Exemplo** (mesma pergunta):

```
Orientações comunitárias › Emergências  [COM-06]

Em desastres e situações de risco, como enchentes, deslizamentos e áreas de
risco, ligue para a Defesa Civil no número 199. Se houver pessoas feridas ou
presas, acione também o Corpo de Bombeiros (193) ou o SAMU (192).

Fonte consultada: Ministério das Comunicações — Emergência: você sabe para quem ligar quando precisa de ajuda?
  https://www.gov.br/mcom/pt-br/noticias/noticias_alt/2026/setembro/emergencia-voce-sabe-para-quem-ligar-quando-precisa-de-ajuda
  Verificado em 18/11/2026

⚠ Aviso: Siga os alertas oficiais da Defesa Civil do seu município e saia de
áreas de risco quando orientado.

Assuntos relacionados para continuar:
  [1] Quais são os telefones de emergência?
  [2] O que devo informar quando ligar para a emergência?
  [3] O que é o CRAS e como ele pode ajudar minha família?
```

## Comparação nos testes

`python src/avaliacao.py` aplica os dois modelos às mesmas 25 perguntas de teste. Depois, verifica automaticamente no texto exibido os critérios que o desafio exige: fonte, aviso, limites e continuidade. O resultado completo está em [`resultados.md`](resultados.md).

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

**Escolha: Modelo B.** Os dois modelos usam exatamente o mesmo conteúdo verificado. A diferença está na clareza e na consistência:

- **Clareza.** O Modelo B diz de onde vem a informação, de quando ela é e o que ainda precisa ser confirmado. Com o Modelo A, o cidadão recebe um parágrafo solto, sem data e sem alerta.
- **Consistência.** O Modelo B tem rótulos fixos (Fonte, Aviso, Assuntos relacionados), então todas as respostas têm a mesma estrutura e o usuário aprende onde procurar cada coisa.
- **Limites.** Quando não há base, o Modelo A só diz "Não encontrei uma resposta". O Modelo B explica o motivo, promete não inventar e mostra caminhos. Esse é o comportamento exigido pelo desafio.

O custo do Modelo B é um texto mais longo, em média 129 palavras contra 55. Para compensar, ele usa blocos curtos com rótulos. O usuário pode alternar para o Modelo A com a opção `[M]` do menu se preferir respostas curtas.

## Se um modelo de linguagem for conectado no futuro

O texto da instrução B foi escrito para servir também como prompt de sistema de um LLM. Nesse caso, o registro encontrado pela busca entraria no contexto do modelo, e a resposta gerada teria de ser confrontada com a base antes de ser exibida, por exemplo conferindo se cita a mesma URL. Essa validação é exigida pelo desafio quando há modelo externo.
