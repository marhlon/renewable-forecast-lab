"""Contraprovas de lacuna, pareamento único, repetição e exposição."""
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from satmon.alarmes_m10_3 import Avaliador, conferir_autoria, iniciar_alarmes


class TestAlarmes(unittest.TestCase):
    def test_passa_contrato_pequeno(self):
        conferir_autoria(iniciar_alarmes)

    def test_eventos_sobrepostos_e_id_com_dois_intervalos(self):
        grid = pd.date_range("2020-01-01", periods=15, freq="15min", tz="UTC")
        valid = np.ones(15, dtype=bool)
        valid[9] = False
        entries = [
            ("A", "channel_50", "Anomaly", 2, 5),
            ("B", "channel_51", "Anomaly", 3, 4),
            ("C", "channel_52", "Anomaly", 9, 9),
            ("D", "channel_52", "Anomaly", 6, 6),
            ("D", "channel_52", "Anomaly", 10, 10),
            ("R", "channel_51", "Rare Event", 7, 7),
        ]
        events = pd.DataFrame([(k, c, cat, grid[a], grid[b]) for k, c, cat, a, b in entries],
                              columns=["ID", "Channel", "Category", "StartTime", "EndTime"])
        ev = Avaliador(grid, valid, events, step_seconds=900)
        a = np.zeros(15, dtype=bool)
        a[[1, 3, 4, 5, 7, 8, 12]] = True
        counts, detail, alarms, channels = ev.avaliar(a, details=True)
        self.assertEqual([r["id_atribuido"] for r in alarms], [None, "B", "A", None, None, None, None])
        self.assertEqual([r["estado"] for r in detail], ["detectado", "detectado", "nao_observavel", "perdido"])
        self.assertEqual(counts["alarmes_repetidos_no_evento"], 1)
        self.assertEqual(counts["alarmes_sem_anotacao"], 3)
        self.assertEqual(counts["alarmes_ignorados_categoria"], 1)
        self.assertAlmostEqual(counts["precisao_por_inicio_avaliavel"], 2/6)
        self.assertAlmostEqual(counts["recall_observaveis"], 2/3)
        self.assertAlmostEqual(counts["recall_todos_ids"], 2/4)
        self.assertAlmostEqual(counts["taxa_sem_anotacao_por_dia"], 3/(7/96))
        self.assertEqual(counts["atraso_mediano_min"], 15)
        self.assertEqual(channels[2]["ids_observaveis"], 1)
        silent = ev.avaliar(np.zeros(15, dtype=bool))
        self.assertEqual(silent["taxa_sem_anotacao_por_dia"], 0)
        self.assertIsNone(silent["precisao_por_inicio_avaliavel"])
        self.assertIsNone(silent["atraso_mediano_min"])

    def test_nao_filtrar_lacunas(self):
        grid = pd.date_range("2020-01-01", periods=3, freq="15min", tz="UTC")[[0, 2]]
        with self.assertRaisesRegex(ValueError, "grade inteira"):
            Avaliador(grid, np.ones(2, dtype=bool), pd.DataFrame(), step_seconds=900)


if __name__ == "__main__":
    unittest.main()
