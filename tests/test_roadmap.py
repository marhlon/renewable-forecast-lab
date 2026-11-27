"""Proteja o fechamento documental sem exigir conclusão de itens planejados."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location(
    "verificar_roadmap", Path(__file__).resolve().parents[1] / "scripts/verificar_roadmap.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RoadmapTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "base.md").write_text("Aceite histórico delimitado.", encoding="utf-8")
        self.data = {
            "schema_version": 1, "updated_at": "2026-11-24", "scope": list(MODULE.MODULOS),
            "items": [self.item(module) for module in MODULE.MODULOS],
        }

    def item(self, module):
        return {
            "id": module + "-01", "modulo": module, "etapa": 1,
            "titulo": "Encerrar evidência faltante", "natureza": "auditoria",
            "estado": "planejado", "constatacao": "Execução ainda não validada.",
            "portoes": ["formacao"], "depende_de": [], "evidencias_base": ["base.md"],
            "entregaveis": [module + "/entrega.md", module + "/revisao.md"],
            "criterios": [{"id": "C1", "descricao": "Conferir a entrega.", "atendido": False}],
            "evidencias": [], "revisao": None, "bloqueio": None,
        }

    def complete(self, item):
        item["estado"] = "validado"
        item["criterios"][0]["atendido"] = True
        for name in item["entregaveis"]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Evidência de teste.", encoding="utf-8")
            item["evidencias"].append({"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "kind": "documento"})
        item["revisao"] = {"responsavel": "Revisor de teste", "data": "2026-11-24", "decisao": "aprovado", "parecer": item["entregaveis"][-1]}

    def validate(self, gate=None):
        return MODULE.validate_backlog(self.data, self.root, gate)

    def assert_error(self, fragment):
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertTrue(any(fragment in message for message in result["errors"]), result)

    def test_planejamento_coerente_passa_sem_simular_conclusao(self):
        before = deepcopy(self.data)
        result = self.validate()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["summary"]["por_estado"]["planejado"], 10)
        self.assertEqual(self.data, before)

    def test_engenharia_encerrada_mantem_operacao_bloqueada_visivel(self):
        for item in self.data["items"][:-1]:
            item["portoes"] = ["engenharia"]
            self.complete(item)
        operational = self.data["items"][-1]
        operational["portoes"] = ["operacao"]
        operational["estado"] = "bloqueado"
        operational["bloqueio"] = {"motivo": "Fonte histórica não comprovada.",
            "condicao_desbloqueio": "Obter evidência da fonte."}
        report = MODULE.validate_backlog(self.data, self.root, gate="engenharia", bloco=1)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(len(report["summary"]["itens_no_gate"]), 9)
        self.assertEqual(report["summary"]["pendencias_fora_do_gate"], [operational["id"]])
        self.assertFalse(MODULE.validate_backlog(self.data, self.root, gate="operacao", bloco=1)["valid"])
        self.assertFalse(MODULE.validate_backlog(self.data, self.root, bloco=1, exigir_fechamento=True)["valid"])

    def test_gate_engenharia_rejeita_sua_propria_pendencia(self):
        self.data["items"][0]["portoes"] = ["engenharia"]
        report = MODULE.validate_backlog(self.data, self.root, gate="engenharia", bloco=1)
        self.assertFalse(report["valid"])
        self.assertIn(self.data["items"][0]["id"], report["summary"]["pendentes_no_gate"])

    def test_gate_engenharia_vazio_nao_pode_ser_apresentado_como_fecho(self):
        result = MODULE.validate_backlog(self.data, self.root, gate="engenharia", bloco=2)
        self.assertFalse(result["valid"])
        self.assertTrue(any("não tem itens" in message for message in result["errors"]))

    def test_gate_explicito_rejeita_itens_abertos(self):
        result = self.validate("formacao")
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["summary"]["pendentes_no_gate"]), 10)

    def test_fecho_sem_evidencia_ou_revisao_e_rejeitado(self):
        self.data["items"][0]["estado"] = "validado"
        self.assert_error("validado exige evidência")

    def test_fecho_com_entregas_hashes_e_revisao_passa(self):
        self.complete(self.data["items"][0])
        result = self.validate()
        self.assertTrue(result["valid"], result["errors"])

    def test_entregavel_faltante_impede_fecho(self):
        item = self.data["items"][0]
        self.complete(item)
        item["entregaveis"].append("M00/resultado_ausente.json")
        self.assert_error("entregaveis")

    def test_entrega_existente_sem_hash_tambem_impede_fecho(self):
        item = self.data["items"][0]
        self.complete(item)
        item["evidencias"].pop(0)
        self.assert_error("entrega sem evidência com hash válido")

    def test_parecer_precisa_ter_hash_nas_evidencias(self):
        item = self.data["items"][0]
        self.complete(item)
        (self.root / "parecer_alternativo.md").write_text("Revisão.", encoding="utf-8")
        item["revisao"]["parecer"] = "parecer_alternativo.md"
        self.assert_error("parecer precisa constar")

    def test_hash_alterado_invalida_evidencia(self):
        item = self.data["items"][0]
        self.complete(item)
        (self.root / item["entregaveis"][0]).write_text("Alterado após o recibo.", encoding="utf-8")
        self.assert_error("hash diverge")

    def test_ciclo_de_dependencias_e_rejeitado(self):
        self.data["items"][0]["depende_de"] = ["M01-01"]
        self.data["items"][1]["depende_de"] = ["M00-01"]
        self.assert_error("ciclo")

    def test_dependencia_inexistente_e_rejeitada(self):
        self.data["items"][0]["depende_de"] = ["M01-99"]
        self.assert_error("ID não encontrado")

    def test_dependencia_aberta_impede_validar_consumidor(self):
        item = self.data["items"][0]
        self.complete(item)
        item["depende_de"] = ["M01-01"]
        self.assert_error("dependência ainda não validada")

    def test_caminhos_externos_e_travessia_sao_rejeitados(self):
        for path in ("../fora.md", "sub/../../fora.md", "C:\\fora.md", "/fora.md", "https://exemplo/arquivo"):
            with self.subTest(path=path):
                self.data["items"][0]["entregaveis"] = [path]
                self.assert_error("caminho relativo")

    def test_link_para_fora_da_raiz_e_rejeitado(self):
        with tempfile.TemporaryDirectory() as outside:
            link = self.root / "externo"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Criação de symlink não permitida neste Windows.")
            self.data["items"][0]["entregaveis"] = ["externo/futuro.md"]
            self.assert_error("resolve fora")

    def test_item_bloqueado_exige_causa_e_desbloqueio(self):
        self.data["items"][0]["estado"] = "bloqueado"
        self.assert_error("item bloqueado exige")

    def test_item_validado_nao_pode_manter_bloqueio_declarado(self):
        item = self.data["items"][0]
        self.complete(item)
        item["bloqueio"] = {"motivo": "Falta confirmação externa.", "condicao_desbloqueio": "Receber confirmação."}
        self.assert_error("validado exige bloqueio null")

    def test_campo_invalido_nao_deve_ser_interpretado_como_criterio_atendido(self):
        item = self.data["items"][0]
        self.complete(item)
        item["criterios"][0]["atendido"] = 1
        self.assert_error("exige booleano")

    def test_cli_grava_sumario_sem_modificar_backlog(self):
        backlog = self.root / "backlog.json"
        backlog.write_text(json.dumps(self.data), encoding="utf-8")
        original = backlog.read_bytes()
        exit_code = MODULE.main(["--root", str(self.root), "--backlog", "backlog.json", "--output", "resumo.json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(backlog.read_bytes(), original)
        self.assertTrue(json.loads((self.root / "resumo.json").read_text(encoding="utf-8"))["valid"])
        self.assertEqual(MODULE.main(["--root", str(self.root), "--backlog", "backlog.json", "--output", "resumo.json"]), 0)
        self.assertEqual(MODULE.main(["--root", str(self.root), "--backlog", "backlog.json", "--output", "backlog.json"]), 1)
        self.assertEqual(backlog.read_bytes(), original)

    def test_cli_nao_sobrescreve_evidencia_nem_outro_arquivo_existente(self):
        item = self.data["items"][0]
        self.complete(item)
        backlog = self.root / "backlog.json"
        backlog.write_text(json.dumps(self.data), encoding="utf-8")
        other = self.root / "resultado_anterior.json"
        other.write_text('{"completed": true}', encoding="utf-8")
        for name in (item["entregaveis"][0], "base.md", "resultado_anterior.json"):
            with self.subTest(path=name):
                path = self.root / name
                before = path.read_bytes()
                self.assertEqual(MODULE.main(["--root", str(self.root), "--backlog", "backlog.json", "--output", name]), 1)
                self.assertEqual(path.read_bytes(), before)

    def test_cli_rejeita_chave_json_repetida(self):
        backlog = self.root / "duplicado.json"
        backlog.write_text('{"schema_version": 1, "schema_version": 1}', encoding="utf-8")
        original = backlog.read_bytes()
        self.assertEqual(MODULE.main(["--root", str(self.root), "--backlog", "duplicado.json"]), 1)
        self.assertEqual(backlog.read_bytes(), original)

    def test_cli_nao_sobrescreve_entrada_por_hardlink(self):
        backlog = self.root / "backlog.json"
        backlog.write_text(json.dumps(self.data), encoding="utf-8")
        alias = self.root / "alias.json"
        try:
            os.link(backlog, alias)
        except (OSError, NotImplementedError):
            self.skipTest("Sistema de arquivos não permite hardlinks.")
        original = backlog.read_bytes()
        self.assertEqual(MODULE.main(["--root", str(self.root), "--backlog", "backlog.json", "--output", "alias.json"]), 1)
        self.assertEqual(backlog.read_bytes(), original)

    def split_stages(self):
        for item, stage in zip(self.data["items"], (1, 2, 3, 4, 5, 6, 7, 8, 9, 9)):
            item["etapa"] = stage

    def test_blocos_filtram_resumo_sem_exigir_fechamento(self):
        self.split_stages()
        for block, expected_stages, count in ((1, [1, 2, 3], 3), (2, [4, 5, 6], 3), (3, [7, 8, 9], 4)):
            with self.subTest(bloco=block):
                result = MODULE.validate_backlog(self.data, self.root, bloco=block)
                self.assertTrue(result["valid"], result["errors"])
                summary = result["summary"]
                self.assertEqual(summary["total_global"], 10)
                self.assertEqual(summary["total"], count)
                self.assertEqual(summary["por_estado"]["planejado"], count)
                self.assertEqual(summary["etapas_do_bloco"], expected_stages)
                self.assertEqual(len(summary["itens_no_bloco"]), count)
                self.assertEqual(set(summary["prontos_para_iniciar"]), set(summary["itens_no_bloco"]))
        self.assertEqual(self.validate()["summary"]["total"], 10)

    def test_filtro_nao_oculta_erro_de_estrutura_em_outro_bloco(self):
        self.split_stages()
        self.data["items"][-1]["entregaveis"] = ["../fora.md"]
        result = MODULE.validate_backlog(self.data, self.root, bloco=1)
        self.assertFalse(result["valid"])
        self.assertTrue(any("M09-01.entregaveis" in message for message in result["errors"]))

    def test_api_rejeita_bloco_invalido_sem_lancar_excecao(self):
        for block in (0, 4, "1", True, [], {}):
            with self.subTest(bloco=block):
                result = MODULE.validate_backlog(self.data, self.root, bloco=block)
                self.assertFalse(result["valid"])
                self.assertTrue(any("bloco:" in message for message in result["errors"]))

    def test_fechamento_exige_bloco_e_booleano_explicitos(self):
        result = MODULE.validate_backlog(self.data, self.root, exigir_fechamento=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("exige --bloco" in message for message in result["errors"]))
        result = MODULE.validate_backlog(self.data, self.root, bloco=1, exigir_fechamento="sim")
        self.assertFalse(result["valid"])
        self.assertTrue(any("exige booleano" in message for message in result["errors"]))

    def test_fecho_de_bloco_rejeita_tambem_pendencias_humanas(self):
        self.split_stages()
        self.complete(self.data["items"][0])
        self.data["items"][1]["estado"] = "aguarda_revisao"
        self.data["items"][2]["estado"] = "bloqueado"
        self.data["items"][2]["bloqueio"] = {"motivo": "Fonte externa ausente.", "condicao_desbloqueio": "Obter comprovação da fonte."}
        result = MODULE.validate_backlog(self.data, self.root, bloco=1, exigir_fechamento=True)
        self.assertFalse(result["valid"])
        self.assertEqual(set(result["summary"]["pendentes_no_bloco"]), {"M01-01", "M02-01"})

    def test_bloco_fechado_nao_exige_que_outros_blocos_estejam_fechados(self):
        self.split_stages()
        for item in self.data["items"][:3]:
            self.complete(item)
        result = MODULE.validate_backlog(self.data, self.root, bloco=1, exigir_fechamento=True)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["summary"]["por_estado"]["validado"], 3)
        self.assertEqual(result["summary"]["total_global"], 10)

    def test_dependencia_de_outro_bloco_precisa_continuar_validada(self):
        self.split_stages()
        for item in self.data["items"][:3]:
            self.complete(item)
        self.data["items"][0]["depende_de"] = ["M09-01"]
        result = MODULE.validate_backlog(self.data, self.root, bloco=1, exigir_fechamento=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("dependência ainda não validada: M09-01" in message for message in result["errors"]))

    def test_prontos_do_bloco_respeitam_dependencia_externa_ao_filtro(self):
        self.split_stages()
        self.data["items"][0]["depende_de"] = ["M09-01"]
        first = MODULE.validate_backlog(self.data, self.root, bloco=1)
        self.assertNotIn("M00-01", first["summary"]["prontos_para_iniciar"])
        self.complete(self.data["items"][-1])
        second = MODULE.validate_backlog(self.data, self.root, bloco=1)
        self.assertIn("M00-01", second["summary"]["prontos_para_iniciar"])
        self.assertNotIn("M09-01", second["summary"]["prontos_para_iniciar"])

    def test_gate_com_bloco_usa_somente_intersecao(self):
        self.split_stages()
        self.complete(self.data["items"][0])
        self.data["items"][1]["portoes"] = ["operacao"]
        self.data["items"][2]["portoes"] = ["operacao"]
        filtered = MODULE.validate_backlog(self.data, self.root, gate="formacao", bloco=1)
        self.assertTrue(filtered["valid"], filtered["errors"])
        self.assertEqual(filtered["summary"]["pendentes_no_gate"], [])
        unfiltered = MODULE.validate_backlog(self.data, self.root, gate="formacao")
        self.assertFalse(unfiltered["valid"])
        self.assertIn("M09-01", unfiltered["summary"]["pendentes_no_gate"])

    def test_cli_filtra_e_so_exige_fecho_quando_solicitado(self):
        self.split_stages()
        backlog = self.root / "backlog.json"
        backlog.write_text(json.dumps(self.data), encoding="utf-8")
        args = ["--root", str(self.root), "--backlog", "backlog.json", "--bloco", "1", "--output", "resumo.json"]
        self.assertEqual(MODULE.main(args), 0)
        self.assertEqual(MODULE.main(args + ["--exigir-fechamento"]), 1)
        summary = json.loads((self.root / "resumo.json").read_text(encoding="utf-8"))["summary"]
        self.assertEqual(summary["total_global"], 10)
        self.assertEqual(summary["total"], 3)


if __name__ == "__main__":
    unittest.main()
