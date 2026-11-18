"""Testes unitários do Citizen Assist AI (biblioteca padrão: unittest).

Rodar a partir da raiz do projeto:  python -m unittest discover tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from base import ErroBase, carregar_base, carregar_json  # noqa: E402
from busca import AMBIGUA, DADOS_PESSOAIS, RESPOSTA, SEM_BASE, VAZIA, buscar  # noqa: E402
from grafo import GrafoAssuntos  # noqa: E402
import respostas as R  # noqa: E402
from sistema import Assistente  # noqa: E402
from texto import contem_dados_pessoais, normalizar, tokenizar  # noqa: E402


def arquivo_temporario(conteudo: str) -> Path:
    arq = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    arq.write(conteudo)
    arq.close()
    return Path(arq.name)


class TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = carregar_base()

    def test_requisitos_minimos_da_base(self):
        self.assertGreaterEqual(len(self.base.registros), 15)
        temas_usados = {r["tema"] for r in self.base.registros}
        self.assertGreaterEqual(len(temas_usados), 3)
        self.assertEqual(self.base.ignorados, [])

    def test_indices(self):
        self.assertEqual(self.base.obter("doc-01")["id"], "DOC-01")
        self.assertIn("DOC-02", self.base.ids_por_palavra("cpf"))
        self.assertIn("Saúde", self.base.subtemas("servicos"))

    def test_arquivo_ausente(self):
        with self.assertRaises(ErroBase):
            carregar_json("/caminho/que/nao/existe.json")

    def test_arquivo_vazio(self):
        with self.assertRaises(ErroBase):
            carregar_json(arquivo_temporario("   "))

    def test_json_invalido(self):
        with self.assertRaises(ErroBase):
            carregar_json(arquivo_temporario("{ isso não é json"))

    def test_registro_inconsistente_e_descartado(self):
        dados = json.loads(Path(__file__).resolve().parent.parent.joinpath("data", "base_conhecimento.json").read_text(encoding="utf-8"))
        dados["registros"].append({"id": "XXX-01", "tema": "documentos"})  # faltam campos
        dados["registros"].append(dict(dados["registros"][0]))             # ID repetido
        base = carregar_base(arquivo_temporario(json.dumps(dados, ensure_ascii=False)))
        self.assertEqual(len(base.registros), 20)
        self.assertTrue(any("XXX-01" in p for p in base.ignorados))
        self.assertTrue(any("repetido" in p for p in base.ignorados))

    def test_sem_registros_validos(self):
        with self.assertRaises(ErroBase):
            carregar_base(arquivo_temporario('{"temas": {"d": "D"}, "registros": [{"id": "X"}]}'))


class TestTexto(unittest.TestCase):
    def test_normalizacao(self):
        self.assertEqual(normalizar("Certidão  de NASCIMENTO!"), "certidao de nascimento")

    def test_tokenizacao_com_sinonimo_e_plural(self):
        self.assertIn("identidade", tokenizar("como tirar o RG"))
        self.assertIn("documento", tokenizar("documentos"))

    def test_dados_pessoais(self):
        self.assertTrue(contem_dados_pessoais("meu cpf 123.456.789-09"))
        self.assertTrue(contem_dados_pessoais("fulano@email.com"))
        self.assertTrue(contem_dados_pessoais("liga (11) 91234-5678"))
        self.assertFalse(contem_dados_pessoais("qual o telefone do 190"))


class TestBusca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = carregar_base()

    def test_pergunta_do_video(self):
        r = buscar(self.base, "Quais documentos consultar antes de solicitar um serviço?")
        self.assertEqual(r.tipo, RESPOSTA)
        self.assertEqual(r.registro["id"], "DOC-01")

    def test_reformulacao(self):
        self.assertEqual(buscar(self.base, "como tirar o novo RG").registro["id"], "DOC-03")

    def test_fora_do_tema(self):
        self.assertEqual(buscar(self.base, "Como funciona um foguete?").tipo, SEM_BASE)

    def test_vazia(self):
        self.assertEqual(buscar(self.base, "   ").tipo, VAZIA)

    def test_ambigua(self):
        r = buscar(self.base, "documento")
        self.assertEqual(r.tipo, AMBIGUA)
        self.assertGreaterEqual(len(r.candidatos), 2)

    def test_dados_pessoais_barrados(self):
        self.assertEqual(buscar(self.base, "cpf 123.456.789-09 está ok?").tipo, DADOS_PESSOAIS)

    def test_ordenacao_por_score(self):
        r = buscar(self.base, "Como faço o cartão do SUS?")
        scores = [s for s, _ in r.candidatos]
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestGrafo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = carregar_base()
        cls.grafo = GrafoAssuntos(cls.base)

    def test_conexo(self):
        self.assertTrue(self.grafo.conexo())

    def test_todo_assunto_tem_tres_vizinhos(self):
        for r in self.base.registros:
            self.assertGreaterEqual(len(self.grafo.vizinhos(r["id"])), 3, r["id"])

    def test_caminho(self):
        self.assertEqual(self.grafo.caminho("DOC-02", "SER-04")[0], "DOC-02")
        self.assertEqual(self.grafo.caminho("DOC-02", "SER-04")[-1], "SER-04")


class TestRespostas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = carregar_base()
        cls.grafo = GrafoAssuntos(cls.base)

    def test_modelo_b_cita_fonte_e_aviso(self):
        r = self.base.obter("DOC-02")
        texto = R.formatar_resposta(r, "Documentos", self.grafo.vizinhos("DOC-02"), "B")
        self.assertIn(r["referencia"]["url"], texto)
        self.assertIn("Verificado em 18/11/2026", texto)
        self.assertIn("Aviso:", texto)
        self.assertIn("Assuntos relacionados", texto)

    def test_sem_base_nao_inventa(self):
        texto = R.formatar_sem_base("x", self.grafo.sugestoes_de_tema(), "B")
        self.assertIn("não vou inventar", texto)
        self.assertNotIn("oficial do Citizen", texto)


class TestSessao(unittest.TestCase):
    def rodar(self, entradas):
        saida = []
        roteiro = iter(entradas)
        Assistente(carregar_base(), entrada=lambda _: next(roteiro), saida=saida.append).executar()
        return "\n".join(saida)

    def test_fluxo_completo_menu_e_navegacao(self):
        texto = self.rodar(["1", "1", "1", "1", "1", "", "S"])
        self.assertIn("[DOC-01]", texto)   # orientação escolhida pelo menu
        self.assertIn("[DOC-02]", texto)   # 1º relacionado
        self.assertIn("[DOC-03]", texto)   # 2º relacionado do DOC-02
        self.assertIn(R.MSG_SAIDA, texto)

    def test_opcao_inexistente_e_vazia(self):
        texto = self.rodar(["9", "", "S"])
        self.assertIn('Opção "9" não existe', texto)
        self.assertIn(R.MSG_VAZIA, texto)

    def test_fim_de_entrada_encerra(self):
        def entrada(_):
            raise EOFError
        saida = []
        Assistente(carregar_base(), entrada=entrada, saida=saida.append).executar()
        self.assertIn(R.MSG_SAIDA, "\n".join(saida))


if __name__ == "__main__":
    unittest.main()
