"""Avaliação do assistente com as perguntas de teste.

Executa cada pergunta de data/perguntas_teste.json, compara o resultado com
o esperado e mede o tempo de consulta. Gera:
  * data/resultados_testes.csv  — registro detalhado (esperado x obtido x acerto x tempo)
  * docs/resultados.md          — indicadores, comparação dos modelos A e B e interpretação

Uso: python src/avaliacao.py
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import RAIZ, carregar_base  # noqa: E402
from busca import AMBIGUA, RESPOSTA, SEM_BASE, buscar  # noqa: E402
from grafo import GrafoAssuntos  # noqa: E402
import respostas as R  # noqa: E402
from sistema import Assistente  # noqa: E402

ARQ_TESTES = RAIZ / "data" / "perguntas_teste.json"
ARQ_CSV = RAIZ / "data" / "resultados_testes.csv"
ARQ_MD = RAIZ / "docs" / "resultados.md"
REPETICOES = 20  # cada consulta é medida 20 vezes; registra-se a média

# Critérios objetivos para comparar os modelos de resposta.
CRITERIOS_RESPOSTA = {
    "cita_fonte": ("Cita o link da fonte", lambda t: "https://" in t),
    "titulo_fonte": ("Identifica a fonte pelo nome", lambda t: "Fonte consultada:" in t),
    "data_verificacao": ("Mostra a data de verificação", lambda t: "Verificado em" in t),
    "aviso": ("Traz aviso de confirmação", lambda t: "Aviso:" in t),
    "localizacao": ("Indica tema e subtema", lambda t: "›" in t),
    "continuidade": ("Oferece assuntos relacionados", lambda t: "relacionados" in t),
}
CRITERIOS_LIMITE = {
    "explica_limite": ("Explica que não há base suficiente", lambda t: "base verificada" in t),
    "nao_inventa": ("Declara que não vai inventar", lambda t: "não vou inventar" in t),
    "sugere_temas": ("Sugere temas ou outra consulta", lambda t: "Você pode tentar" in t),
    "canal_oficial": ("Remete ao canal oficial", lambda t: "canal oficial" in t),
}


def executar_menu(base, entrada: str) -> tuple[str, str]:
    """Executa uma entrada no menu principal e devolve (tipo_obtido, mensagem)."""
    saida: list[str] = []
    roteiro = iter([entrada, "S"])
    assistente = Assistente(base, entrada=lambda _: next(roteiro), saida=saida.append)
    assistente.executar()
    texto = "\n".join(saida)
    if "não existe" in texto:
        return "opcao_invalida", R.MSG_OPCAO_INVALIDA.format(opcao=entrada)
    return "outro", texto[-200:]


def renderizar(base, grafo, resultado, modelo: str) -> str:
    if resultado.tipo == RESPOSTA:
        r = resultado.registro
        return R.formatar_resposta(r, base.temas[r["tema"]], grafo.vizinhos(r["id"]), modelo)
    if resultado.tipo == SEM_BASE:
        return R.formatar_sem_base(resultado.consulta, grafo.sugestoes_de_tema(), modelo)
    if resultado.tipo == AMBIGUA:
        return R.formatar_ambigua([r for _, r in resultado.candidatos], modelo)
    return ""


def resumo_obtido(resultado, texto_menu: str = "") -> str:
    if texto_menu:
        return texto_menu
    if resultado.tipo == RESPOSTA:
        return f"{resultado.registro['id']}: {resultado.registro['pergunta']}"
    if resultado.tipo == AMBIGUA:
        return "Opções: " + ", ".join(r["id"] for _, r in resultado.candidatos)
    return {
        "sem_base": "Aviso de limite + sugestão de temas",
        "vazia": R.MSG_VAZIA,
        "dados_pessoais": "Mensagem descartada por conter dados pessoais",
    }.get(resultado.tipo, resultado.tipo)


def avaliar() -> dict:
    base = carregar_base()
    grafo = GrafoAssuntos(base)
    testes = json.loads(ARQ_TESTES.read_text(encoding="utf-8"))["perguntas"]

    linhas = []
    comparacao = {"A": {}, "B": {}}
    tamanhos = {"A": [], "B": []}
    for t in testes:
        if t["modo"] == "menu":
            inicio = time.perf_counter()
            tipo, texto = executar_menu(base, t["entrada"])
            tempo_ms = (time.perf_counter() - inicio) * 1000
            resultado, score, id_obtido, resumo = None, "", "", texto
        else:
            tempos = []
            for _ in range(REPETICOES):
                inicio = time.perf_counter()
                resultado = buscar(base, t["entrada"])
                renderizar(base, grafo, resultado, "B")
                tempos.append((time.perf_counter() - inicio) * 1000)
            tempo_ms = statistics.mean(tempos)
            tipo = resultado.tipo
            score = f"{resultado.score:.3f}" if resultado.candidatos else ""
            id_obtido = resultado.registro["id"] if resultado.registro else ""
            resumo = resumo_obtido(resultado)
            for modelo in ("A", "B"):
                texto = renderizar(base, grafo, resultado, modelo)
                criterios = CRITERIOS_RESPOSTA if tipo == RESPOSTA else CRITERIOS_LIMITE if tipo == SEM_BASE else {}
                for chave, (_, funcao) in criterios.items():
                    comparacao[modelo].setdefault(chave, []).append(funcao(texto))
                if tipo in (RESPOSTA, SEM_BASE):
                    tamanhos[modelo].append(len(texto.split()))

        acerto = tipo == t["tipo_esperado"] and (t["id_esperado"] in (None, id_obtido))
        linhas.append({
            "id": t["id"],
            "categoria": t["categoria"],
            "entrada": t["entrada"],
            "tipo_esperado": t["tipo_esperado"],
            "id_esperado": t["id_esperado"] or "",
            "orientacao_esperada": t["orientacao_esperada"],
            "tipo_obtido": tipo,
            "id_obtido": id_obtido,
            "resposta_obtida": resumo,
            "score": score,
            "acerto": "acerto" if acerto else "erro",
            "tempo_ms": f"{tempo_ms:.3f}",
        })
    return {"linhas": linhas, "comparacao": comparacao, "tamanhos": tamanhos, "base": base}


def salvar_csv(linhas: list[dict]) -> None:
    with ARQ_CSV.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)


def indicadores(linhas: list[dict]) -> dict:
    total = len(linhas)
    acertos = sum(1 for l in linhas if l["acerto"] == "acerto")
    tempos = [float(l["tempo_ms"]) for l in linhas]
    por_categoria: dict[str, list[int]] = {}
    for l in linhas:
        grupo = "limitações" if l["categoria"].startswith("limitacao") else l["categoria"]
        por_categoria.setdefault(grupo, [0, 0])
        por_categoria[grupo][0] += l["acerto"] == "acerto"
        por_categoria[grupo][1] += 1
    return {
        "total": total,
        "acertos": acertos,
        "taxa": 100 * acertos / total,
        "tempo_medio": statistics.mean(tempos),
        "tempo_max": max(tempos),
        "por_categoria": por_categoria,
    }


def percentual(valores: list[bool]) -> float:
    return 100 * sum(valores) / len(valores) if valores else 0.0


def salvar_md(dados: dict, ind: dict) -> None:
    linhas, comp = dados["linhas"], dados["comparacao"]
    erros = [l for l in linhas if l["acerto"] == "erro"]
    md = [
        "# Resultados dos testes",
        "",
        "> Arquivo gerado automaticamente por `python src/avaliacao.py`. "
        "O registro detalhado está em `data/resultados_testes.csv`.",
        "",
        "## Indicadores",
        "",
        "| Indicador | Valor |",
        "|---|---|",
        f"| Perguntas de teste | {ind['total']} |",
        f"| Classificadas como acerto | {ind['acertos']} |",
        f"| **Taxa de acerto** | **{ind['taxa']:.1f}%** ({ind['acertos']}/{ind['total']}) |".replace('.', ','),
        f"| Tempo médio de consulta | {ind['tempo_medio']:.2f} ms |",
        f"| Maior tempo de consulta | {ind['tempo_max']:.2f} ms |",
        "",
        "Fórmulas: taxa de acerto = acertos ÷ total × 100; tempo médio = média dos tempos medidos.",
        f"Cada consulta foi repetida {REPETICOES} vezes com `time.perf_counter()` (busca + formatação da resposta) "
        "e registrou-se a média; a opção de menu foi medida em uma execução da sessão completa.",
        "",
        "### Acerto por categoria",
        "",
        "| Categoria | Acertos | Total | Taxa |",
        "|---|---|---|---|",
    ]
    for cat, (ac, tot) in ind["por_categoria"].items():
        md.append(f"| {cat} | {ac} | {tot} | {100 * ac / tot:.1f}% |".replace(".", ","))

    md += [
        "",
        "## Registro dos testes",
        "",
        "| ID | Categoria | Entrada | Esperado | Obtido | Resultado | Tempo (ms) |",
        "|---|---|---|---|---|---|---|",
    ]
    for l in linhas:
        esperado = l["id_esperado"] or l["tipo_esperado"]
        obtido = l["id_obtido"] or l["tipo_obtido"]
        entrada = l["entrada"] if l["entrada"] else "(vazia)"
        md.append(f"| {l['id']} | {l['categoria']} | {entrada} | {esperado} | {obtido} | {l['acerto']} | {l['tempo_ms']} |")

    md += ["", "## Comparação dos modelos de instrução (A × B)", "",
           "Os dois modelos foram aplicados às mesmas respostas obtidas nos testes. "
           "Cada critério é verificado automaticamente no texto exibido ao usuário.", "",
           "| Critério | Modelo A | Modelo B |", "|---|---|---|"]
    for criterios in (CRITERIOS_RESPOSTA, CRITERIOS_LIMITE):
        for chave, (rotulo, _) in criterios.items():
            md.append(f"| {rotulo} | {percentual(comp['A'].get(chave, [])):.0f}% | {percentual(comp['B'].get(chave, [])):.0f}% |")
    media_a = statistics.mean(percentual(v) for v in comp["A"].values())
    media_b = statistics.mean(percentual(v) for v in comp["B"].values())
    md += [
        f"| **Média dos critérios** | **{media_a:.0f}%** | **{media_b:.0f}%** |",
        f"| Tamanho médio do texto exibido | {statistics.mean(dados['tamanhos']['A']):.0f} palavras | {statistics.mean(dados['tamanhos']['B']):.0f} palavras |",
        "",
        "Os critérios vêm dos requisitos do desafio (citar a fonte, avisar quando confirmar, informar limites e "
        "oferecer continuidade). Como custo, o Modelo B exibe textos mais longos; para compensar, ele usa blocos "
        "curtos e rótulos fixos (Fonte, Aviso, Assuntos relacionados), que facilitam a leitura em tela.",
        "",
        "**Escolha: Modelo B (padrão do sistema).** O Modelo A só entrega o texto e o link: o cidadão não sabe "
        "de quando é a informação, não recebe o aviso para confirmar requisitos e, quando não há base, recebe "
        "apenas \"Não encontrei uma resposta\", sem caminho para continuar. O Modelo B mantém a mesma orientação "
        "(não acrescenta conteúdo), mas sempre mostra fonte, data de verificação, aviso e próximos passos, o que "
        "torna as respostas mais claras e consistentes entre si.",
        "",
        "## Erros observados",
        "",
    ]
    if erros:
        for l in erros:
            md.append(f"- **{l['id']}** — \"{l['entrada']}\": esperado `{l['id_esperado'] or l['tipo_esperado']}`, "
                      f"obtido `{l['id_obtido'] or l['tipo_obtido']}` (score {l['score']}).")
    else:
        md.append("- Nenhum erro nesta execução.")
    ARQ_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    dados = avaliar()
    ind = indicadores(dados["linhas"])
    salvar_csv(dados["linhas"])
    salvar_md(dados, ind)
    print(f"Perguntas testadas: {ind['total']}")
    print(f"Acertos: {ind['acertos']}  |  Taxa de acerto: {ind['taxa']:.1f}%")
    print(f"Tempo médio de consulta: {ind['tempo_medio']:.2f} ms  |  maior: {ind['tempo_max']:.2f} ms")
    for l in dados["linhas"]:
        if l["acerto"] == "erro":
            print(f"  erro em {l['id']}: esperado {l['id_esperado'] or l['tipo_esperado']}, obtido {l['id_obtido'] or l['tipo_obtido']}")
    print(f"Arquivos gerados: {ARQ_CSV.relative_to(RAIZ)}, {ARQ_MD.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
