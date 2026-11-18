"""Busca de orientações por pergunta livre.

Estratégia (detalhada em docs/estrategia_busca.md):
  1. Validação: entrada vazia ou com dados pessoais é barrada antes da busca.
  2. Normalização e tokenização (texto.tokenizar).
  3. Pré-seleção de candidatos pelo índice invertido (palavra -> IDs) e pelos
     termos das perguntas cadastradas.
  4. Pontuação de cada candidato (0 a 1):
       cobertura  = (2 x termos em palavras_chave + 1 x termos só na pergunta/subtema)
                    / (2 x total de termos da consulta)
       frase      = bônus de 0,25 se uma palavra-chave composta aparece inteira na consulta
       similar    = difflib.SequenceMatcher entre a consulta e a pergunta cadastrada
       score      = min(1, 0,55 x cobertura + 0,25 x similar + frase)
  5. Decisão:
       score do 1º < LIMIAR                                -> sem base suficiente
       1º e 2º com diferença < MARGEM                     -> consulta ambígua
       caso contrário                                       -> resposta com o 1º
     Ordenação: score decrescente; empate desfeito pela ordem do ID.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from base import BaseConhecimento
from texto import contem_dados_pessoais, normalizar, tokenizar

LIMIAR = 0.30
MARGEM_AMBIGUIDADE = 0.08
MAX_CANDIDATOS = 3

RESPOSTA = "resposta"
AMBIGUA = "ambigua"
SEM_BASE = "sem_base"
VAZIA = "vazia"
DADOS_PESSOAIS = "dados_pessoais"


@dataclass
class ResultadoBusca:
    tipo: str
    consulta: str
    termos: list[str] = field(default_factory=list)
    registro: dict | None = None
    candidatos: list[tuple[float, dict]] = field(default_factory=list)

    @property
    def score(self) -> float:
        return self.candidatos[0][0] if self.candidatos else 0.0


def _termos_registro(registro: dict) -> tuple[set[str], set[str], list[str]]:
    """(termos das palavras-chave, termos da pergunta/subtema, frases-chave normalizadas)."""
    chave = {t for termo in registro["palavras_chave"] for t in tokenizar(termo)}
    pergunta = set(tokenizar(registro["pergunta"])) | set(tokenizar(registro["subtema"]))
    frases = [normalizar(t) for t in registro["palavras_chave"] if len(normalizar(t).split()) > 1]
    return chave, pergunta, frases


def pontuar(consulta: str, termos: list[str], registro: dict) -> float:
    q = set(termos)
    if not q:
        return 0.0
    chave, pergunta, frases = _termos_registro(registro)
    em_chave = len(q & chave)
    so_pergunta = len((q & pergunta) - chave)
    cobertura = (2 * em_chave + so_pergunta) / (2 * len(q))
    consulta_norm = normalizar(consulta)
    frase = 0.25 if any(f in consulta_norm for f in frases) else 0.0
    similar = SequenceMatcher(None, consulta_norm, normalizar(registro["pergunta"])).ratio()
    return round(min(1.0, 0.55 * cobertura + 0.25 * similar + frase), 3)


def candidatos(base: BaseConhecimento, termos: list[str]) -> list[dict]:
    """Pré-seleção pelo índice invertido e pelos termos das perguntas cadastradas."""
    ids: set[str] = set()
    for termo in termos:
        ids |= base.ids_por_palavra(termo)
    q = set(termos)
    for r in base.registros:
        if q & set(tokenizar(r["pergunta"])):
            ids.add(r["id"])
    return [base.por_id[i] for i in sorted(ids)]


def buscar(base: BaseConhecimento, consulta: str) -> ResultadoBusca:
    consulta = (consulta or "").strip()
    if not consulta:
        return ResultadoBusca(VAZIA, consulta)
    if contem_dados_pessoais(consulta):
        return ResultadoBusca(DADOS_PESSOAIS, consulta)

    termos = tokenizar(consulta)
    if not termos:
        return ResultadoBusca(SEM_BASE, consulta, termos)

    pontuados = [(pontuar(consulta, termos, r), r) for r in candidatos(base, termos)]
    pontuados.sort(key=lambda par: (-par[0], par[1]["id"]))
    top = pontuados[:MAX_CANDIDATOS]

    if not top or top[0][0] < LIMIAR:
        return ResultadoBusca(SEM_BASE, consulta, termos, None, top)

    if len(top) > 1:
        s1, s2 = top[0][0], top[1][0]
        if s2 >= LIMIAR and s1 - s2 < MARGEM_AMBIGUIDADE:
            opcoes = [par for par in top if par[0] >= LIMIAR and s1 - par[0] < MARGEM_AMBIGUIDADE]
            return ResultadoBusca(AMBIGUA, consulta, termos, None, opcoes)

    return ResultadoBusca(RESPOSTA, consulta, termos, top[0][1], top)
