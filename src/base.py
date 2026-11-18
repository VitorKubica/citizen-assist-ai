"""Carregamento, validação e indexação da base de conhecimento.

A base é um arquivo JSON (data/base_conhecimento.json). Este módulo:
  * lê o arquivo e trata arquivo ausente, vazio ou com JSON inválido;
  * valida os campos obrigatórios de cada registro e a consistência da base
    (IDs únicos, temas conhecidos, relacionados existentes, datas válidas);
  * monta índices em dicionários para recuperar registros por identificador,
    por tema/subtema e por palavra-chave.

Nenhuma regra de busca ou de resposta depende do conteúdo dos registros, por
isso acrescentar ou corrigir orientações exige apenas editar o JSON.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from texto import tokenizar

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_PADRAO = RAIZ / "data" / "base_conhecimento.json"

# Campo -> tipo esperado. Todos são obrigatórios.
CAMPOS_OBRIGATORIOS: dict[str, type] = {
    "id": str,
    "tema": str,
    "subtema": str,
    "pergunta": str,
    "palavras_chave": list,
    "orientacao": str,
    "referencia": dict,
    "data_verificacao": str,
    "aviso": str,
    "relacionados": list,
}
CAMPOS_REFERENCIA = ("titulo", "url")


class ErroBase(Exception):
    """Erro de leitura ou de consistência da base, com mensagem para o usuário."""


def carregar_json(caminho: Path | str = CAMINHO_PADRAO) -> dict:
    """Lê o arquivo JSON tratando ausência, arquivo vazio e sintaxe inválida."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroBase(f"Arquivo da base não encontrado: {caminho}")
    conteudo = caminho.read_text(encoding="utf-8").strip()
    if not conteudo:
        raise ErroBase(f"O arquivo da base está vazio: {caminho}")
    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError as erro:
        raise ErroBase(
            f"O arquivo da base não é um JSON válido (linha {erro.lineno}, coluna {erro.colno})."
        ) from erro
    if not isinstance(dados, dict) or not isinstance(dados.get("registros"), list):
        raise ErroBase("A base precisa ser um objeto com a lista 'registros'.")
    if not isinstance(dados.get("temas"), dict) or not dados["temas"]:
        raise ErroBase("A base precisa declarar o dicionário 'temas'.")
    return dados


def validar_registro(registro: dict, temas: dict) -> list[str]:
    """Devolve a lista de problemas encontrados em um registro (vazia se ok)."""
    problemas: list[str] = []
    rid = registro.get("id", "<sem id>") if isinstance(registro, dict) else "<inválido>"
    if not isinstance(registro, dict):
        return [f"{rid}: o registro não é um objeto JSON."]

    for campo, tipo in CAMPOS_OBRIGATORIOS.items():
        if campo not in registro:
            problemas.append(f"{rid}: campo obrigatório ausente '{campo}'.")
            continue
        valor = registro[campo]
        if not isinstance(valor, tipo):
            problemas.append(f"{rid}: campo '{campo}' deveria ser {tipo.__name__}.")
        elif tipo in (str, list) and len(valor) == 0:
            problemas.append(f"{rid}: campo '{campo}' está vazio.")

    if isinstance(registro.get("tema"), str) and registro["tema"] not in temas:
        problemas.append(f"{rid}: tema desconhecido '{registro['tema']}'.")

    ref = registro.get("referencia")
    if isinstance(ref, dict):
        for campo in CAMPOS_REFERENCIA:
            if not str(ref.get(campo, "")).strip():
                problemas.append(f"{rid}: referência sem '{campo}'.")
        if str(ref.get("url", "")).strip() and not str(ref["url"]).startswith("https://"):
            problemas.append(f"{rid}: a URL da referência deve começar com https://.")

    data = registro.get("data_verificacao")
    if isinstance(data, str):
        try:
            date.fromisoformat(data)
        except ValueError:
            problemas.append(f"{rid}: data_verificacao deve estar no formato AAAA-MM-DD.")

    return problemas


class BaseConhecimento:
    """Base validada com índices em dicionários."""

    def __init__(self, dados: dict):
        self.temas: dict[str, str] = dados["temas"]
        self.registros: list[dict] = []
        self.ignorados: list[str] = []  # problemas de registros descartados

        problemas_gerais: list[str] = []
        vistos: set[str] = set()
        for registro in dados["registros"]:
            problemas = validar_registro(registro, self.temas)
            rid = registro.get("id") if isinstance(registro, dict) else None
            if rid in vistos:
                problemas.append(f"{rid}: ID repetido.")
            if problemas:
                self.ignorados.extend(problemas)
                continue
            vistos.add(rid)
            self.registros.append(registro)

        if not self.registros:
            raise ErroBase("Nenhum registro válido na base. " + " ".join(self.ignorados[:3]))

        # Índice 1: identificador -> registro
        self.por_id: dict[str, dict] = {r["id"]: r for r in self.registros}

        # Relacionados que apontam para IDs inexistentes são removidos e avisados.
        for r in self.registros:
            validos = [x for x in r["relacionados"] if x in self.por_id and x != r["id"]]
            for x in r["relacionados"]:
                if x not in validos:
                    problemas_gerais.append(f"{r['id']}: relacionado inexistente '{x}' ignorado.")
            r["relacionados"] = validos
        self.ignorados.extend(problemas_gerais)

        # Índice 2: tema -> subtema -> lista de IDs (hierarquia, na ordem do arquivo)
        self.por_tema: dict[str, dict[str, list[str]]] = {t: {} for t in self.temas}
        for r in self.registros:
            self.por_tema[r["tema"]].setdefault(r["subtema"], []).append(r["id"])

        # Índice 3: palavra (normalizada) -> conjunto de IDs (índice invertido)
        self.por_palavra: dict[str, set[str]] = {}
        for r in self.registros:
            for termo in r["palavras_chave"]:
                for palavra in tokenizar(termo):
                    self.por_palavra.setdefault(palavra, set()).add(r["id"])

    # ------------------------------------------------------------ consultas
    def obter(self, rid: str) -> dict | None:
        return self.por_id.get(rid.strip().upper())

    def listar_temas(self) -> list[tuple[str, str]]:
        """[(chave, nome)] na ordem declarada no arquivo."""
        return list(self.temas.items())

    def subtemas(self, tema: str) -> list[str]:
        return list(self.por_tema.get(tema, {}).keys())

    def registros_do_subtema(self, tema: str, subtema: str) -> list[dict]:
        return [self.por_id[i] for i in self.por_tema.get(tema, {}).get(subtema, [])]

    def ids_por_palavra(self, palavra: str) -> set[str]:
        return self.por_palavra.get(palavra, set())

    def resumo(self) -> str:
        partes = [f"{nome}: {sum(len(v) for v in self.por_tema[chave].values())}" for chave, nome in self.temas.items()]
        return f"{len(self.registros)} orientações ({', '.join(partes)})"


def carregar_base(caminho: Path | str = CAMINHO_PADRAO) -> BaseConhecimento:
    return BaseConhecimento(carregar_json(caminho))
