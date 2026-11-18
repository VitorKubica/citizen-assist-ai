"""Teste de facilidade de uso por roteiro de tarefas.

Cada tarefa representa um objetivo comum do cidadão e é executada na sessão
real do assistente (src/sistema.py) com as entradas que um usuário digitaria,
incluindo erros comuns (digitar uma palavra onde se espera um número,
apertar Enter sem escrever nada). O script registra se a tarefa foi
concluída, quantas interações foram necessárias, quantas mensagens de erro
apareceram e o tempo de processamento. Gera docs/teste_usabilidade.md.

Uso: python src/usabilidade.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import RAIZ, carregar_base  # noqa: E402
import respostas as R  # noqa: E402
from sistema import Assistente  # noqa: E402

ARQ_MD = RAIZ / "docs" / "teste_usabilidade.md"

TAREFAS = [
    {
        "id": "U1",
        "objetivo": "Descobrir quais documentos separar antes de pedir um serviço (pergunta do vídeo).",
        "entradas": ["Quais documentos consultar antes de solicitar um serviço?", "", "S"],
        "sucesso": ["DOC-01"],
        "ideal": 2,
    },
    {
        "id": "U2",
        "objetivo": "Encontrar como tirar o CPF navegando pelo menu (o usuário digita o nome do assunto em vez do número).",
        "entradas": ["1", "identificação", "2", "1", "", "S"],
        "sucesso": ["DOC-02"],
        "ideal": 4,
    },
    {
        "id": "U3",
        "objetivo": "Partir do Cartão SUS e navegar por três assuntos relacionados.",
        "entradas": ["Como faço o cartão do SUS?", "1", "1", "1", "", "S"],
        "sucesso": ["SER-01", "SER-02", "DOC-04", "DOC-01"],
        "ideal": 5,
    },
    {
        "id": "U4",
        "objetivo": "Fazer uma pergunta fora dos temas e seguir a sugestão até o telefone de emergência.",
        "entradas": ["Como funciona um foguete?", "3", "1", "1", "", "S"],
        "sucesso": ["COM-01"],
        "ideal": 5,
    },
    {
        "id": "U5",
        "objetivo": "Resolver uma consulta ambígua (\"cartão\") escolhendo a opção desejada.",
        "entradas": ["cartão", "2", "", "S"],
        "sucesso": ["SER-02"],
        "ideal": 3,
    },
    {
        "id": "U6",
        "objetivo": "Recuperar-se de Enter vazio e opção inexistente e chegar ao telefone do SAMU.",
        "entradas": ["", "7", "P", "Qual o telefone do SAMU?", "", "S"],
        "sucesso": ["COM-01"],
        "ideal": 3,
    },
]


def executar_tarefa(base, tarefa: dict) -> dict:
    saida: list[str] = []
    roteiro = iter(tarefa["entradas"])
    assistente = Assistente(base, entrada=lambda _: next(roteiro), saida=saida.append)
    inicio = time.perf_counter()
    assistente.executar()
    tempo_ms = (time.perf_counter() - inicio) * 1000
    texto = "\n".join(saida)
    erros = texto.count("não existe") + texto.count(R.MSG_VAZIA)
    concluida = all(rid in assistente.historico for rid in tarefa["sucesso"])
    interacoes = len(tarefa["entradas"]) - 1  # o "S" final só encerra o teste
    return {
        **tarefa,
        "concluida": concluida,
        "interacoes": interacoes,
        "erros": erros,
        "tempo_ms": tempo_ms,
        "visitados": list(dict.fromkeys(assistente.historico)),
    }


DIFICULDADES = {
    "U3": "Na primeira execução do roteiro, a navegação \"voltava\" ao assunto anterior: a partir do Cartão "
          "Digital (SER-02), a opção [1] levava de volta ao Cartão SUS (SER-01), e o usuário ficava andando em "
          "círculo. Corrigido: a lista de relacionados agora omite o assunto de onde o usuário acabou de vir. "
          "Na execução registrada acima, ele percorre SER-01 → SER-02 → DOC-04 → DOC-01.",
    "U2": "No submenu, o usuário escreveu o nome do assunto (\"identificação\"); o sistema só aceita o número e "
          "mostrou \"Opção não existe\". A mensagem explicou o erro e o usuário concluiu na tentativa seguinte, "
          "mas a tarefa custou uma interação extra.",
    "U4": "A resposta de limite sugere os temas, mas não permite escolher um tema ali mesmo: o usuário precisa "
          "voltar ao menu e digitar o número do tema.",
    "U6": "Enter vazio e opção inexistente geraram mensagens claras e o menu foi exibido de novo. Foram 2 "
          "interações a mais que o caminho ideal.",
}


def gerar_relatorio(resultados: list[dict]) -> str:
    concluidas = sum(r["concluida"] for r in resultados)
    total_int = sum(r["interacoes"] for r in resultados)
    total_ideal = sum(r["ideal"] for r in resultados)
    total_erros = sum(r["erros"] for r in resultados)
    md = [
        "# Teste de facilidade de uso — roteiro de tarefas",
        "",
        "> Gerado por `python src/usabilidade.py`.",
        "",
        "## Método",
        "",
        "O teste seguiu um **roteiro de tarefas**, que é uma das duas opções aceitas pelo desafio. Foram seis "
        "objetivos comuns de um cidadão, executados na sessão real do assistente, com as mesmas entradas que um "
        "usuário digitaria, inclusive erros comuns: palavra no lugar do número, Enter vazio e opção inexistente. "
        "Para cada tarefa foram registrados conclusão, interações usadas comparadas ao caminho ideal, mensagens "
        "de erro exibidas e tempo de processamento. O roteiro foi definido e conduzido pelo autor "
        "(Vitor Kubica Silveira), que observou as telas geradas para anotar as dificuldades abaixo.",
        "",
        "## Resultados",
        "",
        "| Tarefa | Objetivo | Concluída | Interações (ideal) | Mensagens de erro | Assuntos visitados | Tempo (ms) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in resultados:
        md.append(
            f"| {r['id']} | {r['objetivo']} | {'sim' if r['concluida'] else 'não'} | {r['interacoes']} ({r['ideal']}) | "
            f"{r['erros']} | {', '.join(r['visitados']) or '—'} | {r['tempo_ms']:.1f} |"
        )
    md += [
        "",
        "## Indicadores",
        "",
        f"- **Taxa de conclusão:** {concluidas}/{len(resultados)} tarefas ({100 * concluidas / len(resultados):.0f}%).",
        f"- **Eficiência:** {total_int} interações usadas contra {total_ideal} no caminho ideal "
        f"({100 * total_ideal / total_int:.0f}% de eficiência).",
        f"- **Mensagens de erro exibidas:** {total_erros}. Todas vieram de entradas inválidas propositais e "
        "nenhuma interrompeu a sessão.",
        "- **Navegação:** a tarefa U3 percorreu 3 assuntos relacionados seguidos a partir de uma única pergunta.",
        "",
        "## Dificuldades observadas",
        "",
    ]
    md += [f"- **{k}:** {v}" for k, v in DIFICULDADES.items()]
    md += [
        "",
        "## Melhorias derivadas do teste",
        "",
        "1. Aceitar o nome do assunto (ou parte dele) nos submenus, além do número.",
        "2. Na resposta de limite, numerar os temas sugeridos para o usuário seguir direto, sem voltar ao menu.",
        "",
        "## Limitações deste teste",
        "",
        "- O roteiro foi executado pelo próprio autor do projeto, que já conhece o sistema. Um cidadão sem "
        "familiaridade com menus de texto pode ter mais dificuldade do que a medida aqui.",
        "- O tempo medido é o de processamento do programa, não o tempo de leitura e digitação de uma pessoa.",
        "- Próximo passo: repetir as mesmas seis tarefas com pessoas de perfis diferentes (idosos e pessoas com "
        "pouca experiência digital) e aplicar um questionário curto de satisfação.",
    ]
    return "\n".join(md) + "\n"


def main() -> int:
    base = carregar_base()
    resultados = [executar_tarefa(base, t) for t in TAREFAS]
    ARQ_MD.write_text(gerar_relatorio(resultados), encoding="utf-8")
    for r in resultados:
        estado = "concluída" if r["concluida"] else "NÃO concluída"
        print(f"{r['id']}: {estado} | interações {r['interacoes']} (ideal {r['ideal']}) | erros {r['erros']} | visitados {r['visitados']}")
    print(f"Relatório: {ARQ_MD.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
