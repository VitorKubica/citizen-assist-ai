"""Citizen Assist AI — interface textual.

Uso:
    python src/sistema.py              # inicia o assistente
    python src/sistema.py --validar    # só valida a base e mostra o resumo
    python src/sistema.py --mapa       # mostra a hierarquia de temas
    python src/sistema.py --modelo A   # inicia com o Modelo A de resposta
    python src/sistema.py --base caminho/arquivo.json

Fluxo: menu de temas ou pergunta livre -> validação da entrada -> busca na
base -> orientação com fonte e aviso (ou aviso de limite) -> assuntos
relacionados para continuar a consulta.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import CAMINHO_PADRAO, BaseConhecimento, ErroBase, carregar_base  # noqa: E402
from busca import AMBIGUA, DADOS_PESSOAIS, RESPOSTA, SEM_BASE, VAZIA, buscar  # noqa: E402
from grafo import GrafoAssuntos  # noqa: E402
import respostas as R  # noqa: E402

Entrada = Callable[[str], str]
Saida = Callable[[str], None]


class Sair(Exception):
    """Encerra a sessão (opção S, Ctrl+C ou fim da entrada)."""


class Assistente:
    def __init__(self, base: BaseConhecimento, entrada: Entrada = input, saida: Saida = print, modelo: str = R.MODELO_PADRAO):
        self.base = base
        self.grafo = GrafoAssuntos(base)
        self._entrada = entrada
        self._saida = saida
        self.modelo = modelo
        self.historico: list[str] = []  # IDs exibidos na sessão (sem dados do usuário)

    # ------------------------------------------------------------ E/S
    def escrever(self, texto: str = "") -> None:
        self._saida(texto)

    def ler(self, rotulo: str) -> str:
        try:
            return self._entrada(rotulo).strip()
        except (EOFError, KeyboardInterrupt):
            raise Sair from None

    def escolher(self, rotulo: str, quantidade: int, letras: dict[str, str], vazio_ok: bool = False) -> int | str | None:
        """Lê uma opção: número de 1..quantidade, uma das letras ou vazio (se permitido).

        Repete a pergunta até receber uma opção válida, explicando o erro.
        """
        while True:
            valor = self.ler(rotulo)
            if not valor:
                if vazio_ok:
                    return None
                self.escrever(R.MSG_VAZIA)
                continue
            if valor.isdigit() and 1 <= int(valor) <= quantidade:
                return int(valor)
            if valor.upper() in letras:
                return valor.upper()
            self.escrever(R.MSG_OPCAO_INVALIDA.format(opcao=valor))

    # ------------------------------------------------------------ telas
    def boas_vindas(self) -> None:
        self.escrever("=" * R.LARGURA)
        self.escrever(R.CABECALHO.center(R.LARGURA))
        self.escrever("=" * R.LARGURA)
        self.escrever(R._quebrar(R.AVISO_NAO_OFICIAL))
        self.escrever(f"Base carregada: {self.base.resumo()}.")

    def menu(self) -> None:
        temas = "  ".join(f"[{i}] {nome}" for i, (_, nome) in enumerate(self.base.listar_temas(), 1))
        self.escrever("")
        self.escrever("Temas: " + temas)
        self.escrever(f"[P] Fazer uma pergunta   [M] Modelo de resposta (atual: {self.modelo})   [S] Sair")

    def executar(self) -> None:
        self.boas_vindas()
        try:
            while True:
                self.menu()
                valor = self.ler("Escolha uma opção ou digite sua pergunta: ")
                self.tratar_opcao_menu(valor)
        except Sair:
            self.escrever("")
            self.escrever(R.MSG_SAIDA)

    def tratar_opcao_menu(self, valor: str) -> None:
        temas = self.base.listar_temas()
        if not valor:
            self.escrever(R.MSG_VAZIA)
        elif valor.isdigit():
            if 1 <= int(valor) <= len(temas):
                self.navegar_tema(temas[int(valor) - 1])
            else:
                self.escrever(R.MSG_OPCAO_INVALIDA.format(opcao=valor))
        elif valor.upper() == "S":
            raise Sair
        elif valor.upper() == "P":
            self.perguntar(self.ler("Digite sua pergunta: "))
        elif valor.upper() == "M":
            self.modelo = "A" if self.modelo == "B" else "B"
            self.escrever(f"Modelo de resposta alterado para {self.modelo}.")
        elif len(valor) <= 2:
            self.escrever(R.MSG_OPCAO_INVALIDA.format(opcao=valor))
        else:
            # Texto livre no menu também é aceito como pergunta.
            self.perguntar(valor)

    def navegar_tema(self, tema: tuple[str, str]) -> None:
        chave, nome = tema
        subtemas = self.base.subtemas(chave)
        self.escrever("")
        self.escrever(f"{nome} — escolha um assunto:")
        for i, sub in enumerate(subtemas, 1):
            self.escrever(f"  [{i}] {sub}")
        op = self.escolher("Número do assunto ([V] voltar): ", len(subtemas), {"V": "voltar"})
        if op == "V":
            return
        registros = self.base.registros_do_subtema(chave, subtemas[op - 1])
        self.escrever("")
        self.escrever(f"{nome} › {subtemas[op - 1]}:")
        for i, r in enumerate(registros, 1):
            self.escrever(f"  [{i}] {r['pergunta']}")
        op = self.escolher("Número da orientação ([V] voltar): ", len(registros), {"V": "voltar"})
        if op == "V":
            return
        self.mostrar(registros[op - 1])

    def perguntar(self, consulta: str) -> None:
        resultado = buscar(self.base, consulta)
        self.escrever("")
        if resultado.tipo == VAZIA:
            self.escrever(R.MSG_VAZIA)
        elif resultado.tipo == DADOS_PESSOAIS:
            self.escrever(R._quebrar(R.MSG_DADOS_PESSOAIS))
        elif resultado.tipo == SEM_BASE:
            self.escrever(R.formatar_sem_base(consulta, self.grafo.sugestoes_de_tema(), self.modelo))
        elif resultado.tipo == AMBIGUA:
            opcoes = [r for _, r in resultado.candidatos]
            self.escrever(R.formatar_ambigua(opcoes, self.modelo))
            op = self.escolher("Número da opção ([Enter] para voltar): ", len(opcoes), {}, vazio_ok=True)
            if op is not None:
                self.mostrar(opcoes[op - 1])
        elif resultado.tipo == RESPOSTA:
            self.mostrar(resultado.registro)

    def mostrar(self, registro: dict) -> None:
        """Exibe a orientação e oferece a navegação pelos assuntos relacionados."""
        anterior: tuple[str, ...] = ()
        while registro is not None:
            self.historico.append(registro["id"])
            # Não oferece de volta o assunto de onde o usuário acabou de vir.
            relacionados = self.grafo.vizinhos(registro["id"], excluir=anterior)
            nome_tema = self.base.temas[registro["tema"]]
            self.escrever("")
            self.escrever("-" * R.LARGURA)
            self.escrever(R.formatar_resposta(registro, nome_tema, relacionados, self.modelo))
            self.escrever("-" * R.LARGURA)
            if not relacionados:
                return
            if self.modelo == "A":
                # O Modelo A não lista relacionados; a navegação fica só no menu.
                return
            op = self.escolher(
                "Número de um assunto relacionado, [P] nova pergunta ou [Enter] para o menu: ",
                len(relacionados), {"P": "pergunta"}, vazio_ok=True,
            )
            if op is None:
                return
            if op == "P":
                self.perguntar(self.ler("Digite sua pergunta: "))
                return
            anterior = (registro["id"],)
            registro = relacionados[op - 1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Citizen Assist AI — assistente de orientação cidadã (não oficial).")
    parser.add_argument("--base", default=str(CAMINHO_PADRAO), help="caminho do arquivo JSON da base")
    parser.add_argument("--modelo", choices=["A", "B"], default=R.MODELO_PADRAO, help="modelo de resposta inicial")
    parser.add_argument("--validar", action="store_true", help="valida a base e sai")
    parser.add_argument("--mapa", action="store_true", help="mostra a hierarquia de temas e sai")
    args = parser.parse_args(argv)

    try:
        base = carregar_base(args.base)
    except ErroBase as erro:
        print(f"Não foi possível iniciar o assistente: {erro}")
        print("Verifique o arquivo da base de conhecimento e tente novamente.")
        return 1

    for problema in base.ignorados:
        print(f"[aviso da base] {problema}")

    if args.validar:
        grafo = GrafoAssuntos(base)
        print(f"Base válida: {base.resumo()}.")
        print(f"Grafo de assuntos conexo: {'sim' if grafo.conexo() else 'não'}.")
        return 0 if not base.ignorados else 2
    if args.mapa:
        print(GrafoAssuntos(base).arvore_texto())
        return 0

    Assistente(base, modelo=args.modelo).executar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
