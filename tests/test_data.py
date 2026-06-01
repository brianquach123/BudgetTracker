import json
import os
import tempfile
import unittest
from unittest.mock import patch

import data as data_mod


def _patched_load(path):
    with patch.object(data_mod, "DATA_FILE", path):
        return data_mod.load_data()


def _patched_save(path, *args):
    with patch.object(data_mod, "DATA_FILE", path):
        data_mod.save_data(*args)


_FULL_ARGS = (
    [{"name": "Netflix", "cost": 15.99, "billing_cycle": "monthly", "charge_day": 1, "card": "Visa"}],
    1200.0, "monthly",
    [{"date": "2024-01-10", "store": "Trader Joe's", "amount": 87.50}],
    3000.0,
    [{"date": "2024-01-05", "amount": 45.00}],
    200.0, "monthly",
    500.0, "weekly",
    300.0, "monthly",
)


class TestLoadDataMissingFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "missing.json")

    def test_returns_empty_subscriptions(self):
        self.assertEqual(_patched_load(self.path)[0], [])

    def test_returns_zero_rent(self):
        self.assertAlmostEqual(_patched_load(self.path)[1], 0.0)

    def test_returns_weekly_rent_cycle_default(self):
        self.assertEqual(_patched_load(self.path)[2], "weekly")

    def test_returns_empty_grocery_receipts(self):
        self.assertEqual(_patched_load(self.path)[3], [])

    def test_returns_zero_paycheck(self):
        self.assertAlmostEqual(_patched_load(self.path)[4], 0.0)

    def test_returns_empty_gas_receipts(self):
        self.assertEqual(_patched_load(self.path)[5], [])

    def test_returns_zero_savings(self):
        self.assertAlmostEqual(_patched_load(self.path)[6], 0.0)

    def test_returns_monthly_savings_cycle_default(self):
        self.assertEqual(_patched_load(self.path)[7], "monthly")

    def test_returns_zero_brokerage(self):
        self.assertAlmostEqual(_patched_load(self.path)[8], 0.0)

    def test_returns_zero_retirement(self):
        self.assertAlmostEqual(_patched_load(self.path)[10], 0.0)


class TestLoadDataLegacyFormats(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write(self, payload):
        path = os.path.join(self.tmpdir, "data.json")
        with open(path, "w") as f:
            json.dump(payload, f)
        return path

    def test_bare_list_returns_defaults(self):
        path = self._write([{"name": "Netflix", "cost": 15.0}])
        result = _patched_load(path)
        self.assertEqual(result[0], [])

    def test_legacy_rent_weekly_key_is_migrated(self):
        path = self._write({"rent_weekly": 500.0})
        result = _patched_load(path)
        self.assertAlmostEqual(result[1], 500.0)

    def test_rent_amount_takes_precedence_over_rent_weekly(self):
        path = self._write({"rent_amount": 600.0, "rent_weekly": 500.0})
        result = _patched_load(path)
        self.assertAlmostEqual(result[1], 600.0)

    def test_missing_keys_use_defaults(self):
        path = self._write({"subscriptions": [], "rent_amount": 800.0})
        result = _patched_load(path)
        self.assertAlmostEqual(result[1], 800.0)
        self.assertAlmostEqual(result[4], 0.0)   # paycheck defaults
        self.assertAlmostEqual(result[6], 0.0)   # savings defaults


class TestSaveAndLoad(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "data.json")

    def _roundtrip(self, *args):
        _patched_save(self.path, *args)
        return _patched_load(self.path)

    def test_subscriptions_roundtrip(self):
        result = self._roundtrip(*_FULL_ARGS)
        self.assertEqual(result[0], _FULL_ARGS[0])

    def test_rent_amount_roundtrip(self):
        result = self._roundtrip(*_FULL_ARGS)
        self.assertAlmostEqual(result[1], 1200.0)

    def test_rent_cycle_roundtrip(self):
        result = self._roundtrip(*_FULL_ARGS)
        self.assertEqual(result[2], "monthly")

    def test_grocery_receipts_roundtrip(self):
        result = self._roundtrip(*_FULL_ARGS)
        self.assertEqual(len(result[3]), 1)
        self.assertAlmostEqual(result[3][0]["amount"], 87.50)

    def test_paycheck_roundtrip(self):
        result = self._roundtrip(*_FULL_ARGS)
        self.assertAlmostEqual(result[4], 3000.0)

    def test_gas_receipts_roundtrip(self):
        result = self._roundtrip(*_FULL_ARGS)
        self.assertEqual(len(result[5]), 1)
        self.assertAlmostEqual(result[5][0]["amount"], 45.0)

    def test_savings_roundtrip(self):
        result = self._roundtrip(*_FULL_ARGS)
        self.assertAlmostEqual(result[6], 200.0)
        self.assertEqual(result[7], "monthly")

    def test_brokerage_roundtrip(self):
        result = self._roundtrip(*_FULL_ARGS)
        self.assertAlmostEqual(result[8], 500.0)
        self.assertEqual(result[9], "weekly")

    def test_retirement_roundtrip(self):
        result = self._roundtrip(*_FULL_ARGS)
        self.assertAlmostEqual(result[10], 300.0)
        self.assertEqual(result[11], "monthly")

    def test_output_is_valid_json(self):
        _patched_save(self.path, *_FULL_ARGS)
        with open(self.path) as f:
            parsed = json.load(f)
        self.assertIn("subscriptions", parsed)
        self.assertIn("paycheck_biweekly", parsed)

    def test_save_overwrites_previous(self):
        _patched_save(self.path, *_FULL_ARGS)
        new_args = list(_FULL_ARGS)
        new_args[1] = 999.0  # different rent
        _patched_save(self.path, *new_args)
        result = _patched_load(self.path)
        self.assertAlmostEqual(result[1], 999.0)


if __name__ == "__main__":
    unittest.main()
