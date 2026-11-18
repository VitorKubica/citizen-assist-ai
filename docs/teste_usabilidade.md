# Teste de facilidade de uso — roteiro de tarefas

> Gerado por `python src/usabilidade.py`.

## Método

O teste seguiu um **roteiro de tarefas**, que é uma das duas opções aceitas pelo desafio. Foram seis objetivos comuns de um cidadão, executados na sessão real do assistente, com as mesmas entradas que um usuário digitaria, inclusive erros comuns: palavra no lugar do número, Enter vazio e opção inexistente. Para cada tarefa foram registrados conclusão, interações usadas comparadas ao caminho ideal, mensagens de erro exibidas e tempo de processamento. O roteiro foi definido e conduzido pelo autor (Vitor Kubica Silveira), que observou as telas geradas para anotar as dificuldades abaixo.

## Resultados

| Tarefa | Objetivo | Concluída | Interações (ideal) | Mensagens de erro | Assuntos visitados | Tempo (ms) |
|---|---|---|---|---|---|---|
| U1 | Descobrir quais documentos separar antes de pedir um serviço (pergunta do vídeo). | sim | 2 (2) | 0 | DOC-01 | 1.3 |
| U2 | Encontrar como tirar o CPF navegando pelo menu (o usuário digita o nome do assunto em vez do número). | sim | 5 (4) | 1 | DOC-02 | 0.2 |
| U3 | Partir do Cartão SUS e navegar por três assuntos relacionados. | sim | 5 (5) | 0 | SER-01, SER-02, DOC-04, DOC-01 | 1.2 |
| U4 | Fazer uma pergunta fora dos temas e seguir a sugestão até o telefone de emergência. | sim | 5 (5) | 0 | COM-01 | 0.5 |
| U5 | Resolver uma consulta ambígua ("cartão") escolhendo a opção desejada. | sim | 3 (3) | 0 | SER-02 | 0.7 |
| U6 | Recuperar-se de Enter vazio e opção inexistente e chegar ao telefone do SAMU. | sim | 5 (3) | 2 | COM-01 | 0.6 |

## Indicadores

- **Taxa de conclusão:** 6/6 tarefas (100%).
- **Eficiência:** 25 interações usadas contra 22 no caminho ideal (88% de eficiência).
- **Mensagens de erro exibidas:** 3. Todas vieram de entradas inválidas propositais e nenhuma interrompeu a sessão.
- **Navegação:** a tarefa U3 percorreu 3 assuntos relacionados seguidos a partir de uma única pergunta.

## Dificuldades observadas

- **U3:** Na primeira execução do roteiro, a navegação "voltava" ao assunto anterior: a partir do Cartão Digital (SER-02), a opção [1] levava de volta ao Cartão SUS (SER-01), e o usuário ficava andando em círculo. Corrigido: a lista de relacionados agora omite o assunto de onde o usuário acabou de vir. Na execução registrada acima, ele percorre SER-01 → SER-02 → DOC-04 → DOC-01.
- **U2:** No submenu, o usuário escreveu o nome do assunto ("identificação"); o sistema só aceita o número e mostrou "Opção não existe". A mensagem explicou o erro e o usuário concluiu na tentativa seguinte, mas a tarefa custou uma interação extra.
- **U4:** A resposta de limite sugere os temas, mas não permite escolher um tema ali mesmo: o usuário precisa voltar ao menu e digitar o número do tema.
- **U6:** Enter vazio e opção inexistente geraram mensagens claras e o menu foi exibido de novo. Foram 2 interações a mais que o caminho ideal.

## Melhorias derivadas do teste

1. Aceitar o nome do assunto (ou parte dele) nos submenus, além do número.
2. Na resposta de limite, numerar os temas sugeridos para o usuário seguir direto, sem voltar ao menu.

## Limitações deste teste

- O roteiro foi executado pelo próprio autor do projeto, que já conhece o sistema. Um cidadão sem familiaridade com menus de texto pode ter mais dificuldade do que a medida aqui.
- O tempo medido é o de processamento do programa, não o tempo de leitura e digitação de uma pessoa.
- Próximo passo: repetir as mesmas seis tarefas com pessoas de perfis diferentes (idosos e pessoas com pouca experiência digital) e aplicar um questionário curto de satisfação.
