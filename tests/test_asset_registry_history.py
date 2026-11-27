from copy import deepcopy
import unittest
from renewable_forecast.asset_registry_history import selecionar_cadastro_causal

def row(**kw):
    return dict({"asset_id":"A","version":"v1","valid_from":"2026-01-01T00:00:00Z",
        "valid_to":None,"known_from":"2026-02-01T00:00:00Z","known_to":None,
        "historical_validity_verified":True,"payload":{"capacity":10}}, **kw)

class CadastroHistoryTests(unittest.TestCase):
    def select(self, records, known="2026-03-01T00:00:00Z", valid="2026-01-10T00:00:00Z"):
        return selecionar_cadastro_causal(records,instante=valid,conhecido_em=known)
    def test_future_correction_preserves_past(self):
        a=row(); b=row(version="v2",known_from="2026-04-01T00:00:00Z",payload={"capacity":20})
        self.assertEqual(self.select([a]),self.select([a,b]))
        self.assertEqual(self.select([a,b],known="2026-05-01T00:00:00Z")[0]["version"],"v2")
    def test_unknown_validity_is_not_invented(self):
        self.assertEqual(self.select([row(valid_from=None,historical_validity_verified=False)]),[])
    def test_half_open_intervals(self):
        a=row(valid_to="2026-01-10T00:00:00Z")
        self.assertEqual(self.select([a]),[])
        b=row(known_to="2026-03-01T00:00:00Z")
        self.assertEqual(self.select([b]),[])
    def test_input_and_nested_output_independent(self):
        records=[row()]; original=deepcopy(records); output=self.select(records)
        output[0]["payload"]["capacity"]=99
        self.assertEqual(records,original)
    def test_reject_ambiguity_duplicate_and_naive(self):
        for records in ([row(),row()], [row(),row(version="v2")], [row(known_from="2026-01-01")]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                self.select(records)
    def test_cannot_claim_verification_with_missing_start(self):
        with self.assertRaises(ValueError):
            self.select([row(valid_from=None)])

if __name__=="__main__":
    unittest.main()
