"""Normalização de texto usada pela base e pela busca.

Etapas: minúsculas -> remoção de acentos -> troca de pontuação por espaço ->
remoção de palavras vazias (stopwords) -> redução simples de plural ->
substituição de sinônimos por um termo canônico.
"""

from __future__ import annotations

import re
import unicodedata

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "pelo", "pela", "para", "pra", "com", "sem",
    "e", "ou", "que", "qual", "quais", "como", "onde", "quando", "quanto", "se", "eu",
    "me", "meu", "minha", "meus", "minhas", "voce", "seu", "sua", "isso", "esse", "essa",
    "este", "esta", "ao", "aos", "sobre", "ser", "ter", "tem", "tenho", "faco", "fazer",
    "posso", "pode", "preciso", "quero", "devo", "e", "ja", "mais", "muito", "algum",
    "alguma", "la", "aqui", "ate", "depois", "antes", "nao", "sim", "ola", "oi", "bom", "dia",
    "boa", "tarde", "noite", "favor", "obrigado", "obrigada", "the", "num", "numa",
    "consigo", "conseguir", "saber", "gostaria", "existe", "ha", "foi", "fui", "estou",
}

# Termo digitado pelo cidadão -> termo usado na base (aplicado depois da normalização).
SINONIMOS = {
    "rg": "identidade",
    "carteira identidade": "identidade",
    "ci": "identidade",
    "cin": "identidade",
    "titulo": "titulo",
    "eleitoral": "eleitor",
    "votar": "eleitor",
    "voto": "eleitor",
    "certidao": "certidao",
    "registro": "registro",
    "demitido": "demissao",
    "demitiram": "demissao",
    "mandaram": "demissao",
    "desempregado": "desemprego",
    "desemprego": "desemprego",
    "sus": "sus",
    "saude": "saude",
    "posto": "sus",
    "ambulancia": "samu",
    "socorro": "emergencia",
    "urgencia": "emergencia",
    "bombeiro": "bombeiros",
    "fogo": "incendio",
    "alagamento": "enchente",
    "inundacao": "enchente",
    "inundou": "enchente",
    "alagou": "enchente",
    "chuva": "enchente",
    "desabamento": "deslizamento",
    "idosa": "idoso",
    "velho": "idoso",
    "agredida": "agressao",
    "apanhou": "agressao",
    "bateu": "agressao",
    "marido": "domestica",
    "reclamar": "reclamacao",
    "devolver": "devolver",
    "devolucao": "devolver",
    "arrependi": "arrependimento",
    "desistir": "desistir",
    "bolsa": "bolsa",
    "aposentar": "aposentadoria",
    "aposentado": "aposentadoria",
    "ctps": "trabalho",
    "govbr": "gov",
    "gov.br": "gov",
}


def remover_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    """Texto em minúsculas, sem acentos e sem pontuação, com espaços simples."""
    texto = remover_acentos(texto.lower())
    texto = texto.replace("gov.br", "gov")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _singular(palavra: str) -> str:
    """Redução simples de plural (suficiente para o vocabulário da base)."""
    if len(palavra) <= 3 or palavra.isdigit():
        return palavra
    for fim, troca in (("coes", "cao"), ("soes", "sao"), ("oes", "ao"), ("aes", "ao"), ("is", "l"), ("ns", "m")):
        if palavra.endswith(fim) and len(palavra) > len(fim) + 2:
            return palavra[: -len(fim)] + troca
    if palavra.endswith("es") and palavra[-3] in "rzs":
        return palavra[:-2]
    if palavra.endswith("s"):
        return palavra[:-1]
    return palavra


def tokenizar(texto: str) -> list[str]:
    """Lista de termos relevantes (sem stopwords, no singular, com sinônimos)."""
    normal = normalizar(texto)
    for frase, troca in (("carteira de identidade", "carteira identidade"),):
        normal = normal.replace(frase, troca)
    termos: list[str] = []
    for palavra in normal.split():
        if palavra in STOPWORDS:
            continue
        palavra = SINONIMOS.get(palavra, palavra)
        palavra = _singular(palavra)
        if palavra and palavra not in STOPWORDS:
            termos.append(palavra)
    return termos


# Padrões que indicam dados pessoais digitados por engano.
PADROES_DADOS_PESSOAIS = [
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),            # CPF
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),                     # e-mail
    re.compile(r"\(?\b\d{2}\)?\s?9?\d{4}-?\d{4}\b"),             # telefone
]


def contem_dados_pessoais(texto: str) -> bool:
    return any(p.search(texto) for p in PADROES_DADOS_PESSOAIS)
