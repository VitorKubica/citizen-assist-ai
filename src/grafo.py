"""Organização dos assuntos: hierarquia (árvore) e grafo de relacionados.

* Hierarquia: tema -> subtema -> orientações. Vem do índice base.por_tema e
  é usada na navegação pelo menu.
* Grafo simples, não direcionado: cada orientação é um vértice. Há uma
  aresta entre A e B quando A lista B em "relacionados", ou o contrário.
  As arestas ligam assuntos que o cidadão costuma precisar em sequência,
  como CPF -> conta gov.br -> Meu INSS. É com o grafo que o assistente
  sugere os próximos passos e permite navegar por vários assuntos
  relacionados.
"""

from __future__ import annotations

from collections import deque

from base import BaseConhecimento


class GrafoAssuntos:
    def __init__(self, base: BaseConhecimento):
        self.base = base
        # Lista de adjacência: id -> lista ordenada de vizinhos
        adj: dict[str, set[str]] = {r["id"]: set() for r in base.registros}
        for r in base.registros:
            for outro in r["relacionados"]:
                adj[r["id"]].add(outro)
                adj[outro].add(r["id"])
        self.adjacencia: dict[str, list[str]] = {}
        for rid, viz in adj.items():
            # Primeiro os relacionados declarados no registro (na ordem do
            # arquivo), depois as ligações que vieram de outros registros.
            declarados = [x for x in base.por_id[rid]["relacionados"] if x in viz]
            extras = sorted(viz - set(declarados))
            self.adjacencia[rid] = declarados + extras

    def vizinhos(self, rid: str, limite: int = 3, excluir: tuple[str, ...] = ()) -> list[dict]:
        """Até `limite` assuntos ligados a `rid`, sem os IDs de `excluir` (ex.: o assunto anterior)."""
        ids = [i for i in self.adjacencia.get(rid, []) if i not in excluir]
        return [self.base.por_id[i] for i in ids[:limite]]

    def caminho(self, origem: str, destino: str) -> list[str]:
        """Menor caminho entre dois assuntos (busca em largura). Lista vazia se não houver."""
        if origem not in self.adjacencia or destino not in self.adjacencia:
            return []
        anteriores: dict[str, str | None] = {origem: None}
        fila = deque([origem])
        while fila:
            atual = fila.popleft()
            if atual == destino:
                break
            for viz in self.adjacencia[atual]:
                if viz not in anteriores:
                    anteriores[viz] = atual
                    fila.append(viz)
        if destino not in anteriores:
            return []
        caminho, no = [], destino
        while no is not None:
            caminho.append(no)
            no = anteriores[no]
        return caminho[::-1]

    def alcancaveis(self, origem: str, profundidade: int = 2) -> list[str]:
        """Assuntos alcançáveis em até `profundidade` passos (sem a origem)."""
        visitados = {origem: 0}
        fila = deque([origem])
        while fila:
            atual = fila.popleft()
            if visitados[atual] == profundidade:
                continue
            for viz in self.adjacencia[atual]:
                if viz not in visitados:
                    visitados[viz] = visitados[atual] + 1
                    fila.append(viz)
        return [i for i in visitados if i != origem]

    def conexo(self) -> bool:
        """True se todos os assuntos estão ligados (navegação sem becos)."""
        if not self.adjacencia:
            return True
        inicio = next(iter(self.adjacencia))
        return len(self.alcancaveis(inicio, profundidade=len(self.adjacencia))) == len(self.adjacencia) - 1

    def sugestoes_de_tema(self) -> list[str]:
        """Sugestões gerais quando não há resposta: tema + seus subtemas."""
        return [
            f"{nome}: {', '.join(self.base.subtemas(chave))}"
            for chave, nome in self.base.listar_temas()
        ]

    def arvore_texto(self) -> str:
        """Hierarquia completa em texto (usada na documentação e no --mapa)."""
        linhas = ["Citizen Assist AI"]
        temas = self.base.listar_temas()
        for i, (chave, nome) in enumerate(temas):
            ultimo_tema = i == len(temas) - 1
            linhas.append(("└── " if ultimo_tema else "├── ") + nome)
            subtemas = self.base.subtemas(chave)
            for j, sub in enumerate(subtemas):
                ultimo_sub = j == len(subtemas) - 1
                pre = "    " if ultimo_tema else "│   "
                linhas.append(pre + ("└── " if ultimo_sub else "├── ") + sub)
                regs = self.base.registros_do_subtema(chave, sub)
                for k, r in enumerate(regs):
                    pre2 = pre + ("    " if ultimo_sub else "│   ")
                    linhas.append(pre2 + ("└── " if k == len(regs) - 1 else "├── ") + f"[{r['id']}] {r['pergunta']}")
        return "\n".join(linhas)
