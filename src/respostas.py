"""Modelos de instrução de resposta e mensagens do assistente.

O protótipo não usa um modelo de linguagem externo. Os dois modelos abaixo
são instruções de resposta (prompts) aplicadas de forma determinística: o
texto de cada instrução define papel, formato e regras, e a função de
formatação correspondente implementa exatamente essas regras sobre o
registro encontrado na base. Assim a resposta nunca contém informação que
não esteja na base verificada. A comparação entre os modelos está em
docs/prompts.md e docs/resultados.md.
"""

from __future__ import annotations

import textwrap
from datetime import date

LARGURA = 78

INSTRUCAO_A = """\
[Modelo A — Resposta direta]
Papel: assistente que responde perguntas do cidadão.
Formato: um parágrafo com a orientação encontrada, seguido do link da fonte.
Regras: usar o texto da orientação da base."""

INSTRUCAO_B = """\
[Modelo B — Orientação estruturada e verificável]
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
  - se a pergunta for ambígua, liste as opções e peça para o cidadão escolher."""

MODELOS = {"A": INSTRUCAO_A, "B": INSTRUCAO_B}
MODELO_PADRAO = "B"

CABECALHO = "Citizen Assist AI · assistente não oficial"
AVISO_NAO_OFICIAL = (
    "Este assistente organiza orientações de fontes públicas e não é canal oficial "
    "de nenhum órgão. Não digite dados pessoais (CPF, telefone, e-mail, endereço)."
)


def _quebrar(texto: str, recuo: str = "") -> str:
    return textwrap.fill(texto, width=LARGURA, initial_indent=recuo, subsequent_indent=recuo)


def _data_br(iso: str) -> str:
    try:
        return date.fromisoformat(iso).strftime("%d/%m/%Y")
    except ValueError:
        return iso


# ------------------------------------------------------------ respostas
def formatar_resposta(registro: dict, nome_tema: str, relacionados: list[dict], modelo: str = MODELO_PADRAO) -> str:
    if modelo == "A":
        return _quebrar(registro["orientacao"]) + "\nFonte: " + registro["referencia"]["url"]

    linhas = [
        f"{nome_tema} › {registro['subtema']}  [{registro['id']}]",
        "",
        _quebrar(registro["orientacao"]),
        "",
        "Fonte consultada: " + registro["referencia"]["titulo"],
        "  " + registro["referencia"]["url"],
        "  Verificado em " + _data_br(registro["data_verificacao"]),
        "",
        _quebrar("⚠ Aviso: " + registro["aviso"]),
    ]
    if relacionados:
        linhas += ["", "Assuntos relacionados para continuar:"]
        linhas += [f"  [{i}] {r['pergunta']}" for i, r in enumerate(relacionados, 1)]
    return "\n".join(linhas)


def formatar_sem_base(consulta: str, sugestoes: list[str], modelo: str = MODELO_PADRAO) -> str:
    if modelo == "A":
        return "Não encontrei uma resposta."
    linhas = [
        _quebrar(
            "Não encontrei na base verificada uma orientação confiável para essa pergunta. "
            "Para não correr o risco de passar uma informação errada, não vou inventar uma resposta."
        ),
        "",
        "Você pode tentar:",
        "  • reformular a pergunta com outras palavras (ex.: \"como tirar o CPF\");",
        "  • navegar pelos temas disponíveis:",
    ]
    linhas += [f"      - {s}" for s in sugestoes]
    linhas += ["  • procurar o canal oficial do órgão responsável pelo assunto."]
    return "\n".join(linhas)


def formatar_ambigua(opcoes: list[dict], modelo: str = MODELO_PADRAO) -> str:
    if modelo == "A":
        return "Encontrei mais de uma resposta: " + "; ".join(r["pergunta"] for r in opcoes)
    linhas = ["Sua pergunta pode se referir a assuntos diferentes. Qual deles você procura?"]
    linhas += [f"  [{i}] {r['pergunta']}" for i, r in enumerate(opcoes, 1)]
    return "\n".join(linhas)


# ------------------------------------------------------------ mensagens de erro
MSG_VAZIA = "Você não digitou nada. Escreva uma pergunta ou escolha uma opção do menu."
MSG_OPCAO_INVALIDA = "Opção \"{opcao}\" não existe. Digite um dos números ou letras mostrados entre colchetes."
MSG_DADOS_PESSOAIS = (
    "Parece que a mensagem contém dados pessoais (CPF, telefone ou e-mail). "
    "Por segurança ela foi descartada e não foi registrada. Reescreva a pergunta "
    "sem informações pessoais, por exemplo: \"como regularizar o CPF\"."
)
MSG_SAIDA = "Até logo! Lembre-se de confirmar as orientações nos canais oficiais."
