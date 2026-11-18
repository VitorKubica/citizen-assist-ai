# Uso de inteligência artificial e validação crítica

## O protótipo usa IA externa?

**Não.** O Citizen Assist AI não chama nenhuma API de modelo de linguagem, nem paga nem gratuita. Também não treina modelos. Ele funciona apenas com Python e a biblioteca padrão. As respostas são sempre trechos de registros da base verificada (`data/base_conhecimento.json`), selecionados por regras de busca e apresentados conforme o modelo de instrução escolhido (veja [`prompts.md`](prompts.md)).

O nome "AI" se refere ao comportamento de assistente: interpretar a pergunta, buscar, decidir e responder com fonte e limites. Não se refere a um modelo generativo.

## Validação crítica: problemas encontrados e decisões

1. **Informação não confirmada não entra.** A página do seguro-desemprego não informa o prazo para pedir o benefício, e o rascunho inicial incluía um prazo. Ele foi retirado e trocado por um aviso para confirmar no 158 ou no portal.
2. **Fonte bloqueada ou que exige login.** A página federal do PAIF exigia autenticação no dia da verificação. A referência do registro do CRAS passou a ser a página pública da Prefeitura de São Paulo, e o texto foi reescrito para refletir só o que essa página diz.
3. **Números do vídeo.** O vídeo mostra a taxa de 83,3% do **exemplo do enunciado**, marcada como ilustrativa. A taxa real medida pelo sistema é **96,0% (24/25)** e está registrada em [`resultados.md`](resultados.md).
4. **Erro mantido na avaliação.** A pergunta T16 ("Dá para mostrar o cartão do SUS pelo celular?") retornou o Cartão SUS (SER-01) em vez do Meu SUS Digital (SER-02). O caso foi mantido no relatório como evidência de uma limitação da busca lexical. A correção proposta está nas melhorias do README.
5. **Defeito de navegação encontrado no teste de uso.** O roteiro de usabilidade revelou que a navegação por relacionados podia voltar ao assunto anterior. O defeito foi corrigido no commit `fix(navegacao)` e registrado em [`teste_usabilidade.md`](teste_usabilidade.md).

## Responsabilidade

- O assistente se apresenta sempre como **não oficial** e não promete integração com órgãos públicos.
- Mensagens com padrões de dados pessoais (CPF, e-mail, telefone) são descartadas, e nada digitado pelo usuário é gravado em arquivo.
- Toda resposta tem fonte, data de verificação e aviso para confirmar requisitos atualizados.
