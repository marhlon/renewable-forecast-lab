"""Exercita a equivalência entre janelas e existência de um início de alarme."""
from itertools import product
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from satmon.alarmes_m10_3 import Avaliador, iniciar_alarmes
from satmon.diagnostico_m10_4 import limite_confirmacao, limites_por_id, perfil_temporal


class DiagnosticoTest(unittest.TestCase):
    def test_limite_equivale_a_existencia_de_inicio_e_desempata_pelo_primeiro(self):
        for n in range(5):
            for values in product([None, -1., 0., 1.], repeat=n):
                u = np.array([item is not None for item in values], dtype=bool)
                s = np.array([-800. if item is None else item for item in values])
                for k in range(1, n + 2):
                    candidates = [(min(values[i-k+1:i+1]), i) for i in range(k-1, n)
                                  if all(v is not None for v in values[i-k+1:i+1])]
                    bound, index = max(candidates, key=lambda c: (c[0], -c[1])) if candidates else (None, None)
                    got = limite_confirmacao(s, u, consecutivos=k)
                    self.assertEqual(got, {"limiar_maximo": bound, "indice_confirmacao": index})
                    if bound is not None:
                        for threshold, expected in ((bound, True), (np.nextafter(bound, np.inf), False)):
                            starts = iniciar_alarmes(s, u, limiar=threshold, consecutivos=k)
                            self.assertEqual(bool(starts.any()), expected)
                            if expected:
                                self.assertEqual(int(np.flatnonzero(starts)[0]), index)

    def test_um_limite_dentro_do_evento_nao_garante_atribuicao(self):
        s = np.array([.8, .9, .95, .97])
        u = np.ones(4, dtype=bool)
        t = pd.date_range("2008-01-01", periods=4, freq="15min", tz="UTC")
        events = pd.DataFrame([["teste", "channel_50", "Anomaly", t[2], t[3]]],
                              columns=["ID", "Channel", "Category", "StartTime", "EndTime"])
        ev = Avaliador(t, u, events, step_seconds=900)
        totals, details, _, _ = ev.avaliar(iniciar_alarmes(s, u, limiar=.8, consecutivos=2), details=True)
        row = next(limites_por_id(s, ev, details, limite_confirmacao, 2))
        self.assertEqual(row["s2_no_id"], .95)
        self.assertEqual(row["estado"], "perdido")
        self.assertEqual(totals["alarmes_sem_anotacao"], 1)

    def test_perfil_anual_nao_une_slots_de_anos_diferentes(self):
        t = pd.date_range("2008-12-31 23:45", periods=2, freq="15min", tz="UTC")
        u = np.ones(2, dtype=bool)
        ev = Avaliador(t, u, pd.DataFrame(columns=["ID", "Channel", "Category", "StartTime", "EndTime"]),
                       step_seconds=900)
        scores = np.array([1., 1.])
        rows, _, _ = perfil_temporal("dev", np.ones((2, 3)), scores, ev, .8, limite_confirmacao, 2)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["s2"] is None for row in rows))
        self.assertEqual(limite_confirmacao(scores, u, consecutivos=2)["limiar_maximo"], 1.)


if __name__ == "__main__":
    unittest.main()
