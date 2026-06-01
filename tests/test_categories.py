import unittest
from abc import ABC

from categories import InvestmentCategory, Savings, Brokerage, Retirement


class TestInvestmentCategoryAbstract(unittest.TestCase):
    def test_cannot_instantiate_base_class(self):
        with self.assertRaises(TypeError):
            InvestmentCategory()

    def test_savings_is_concrete(self):
        s = Savings()
        self.assertIsInstance(s, InvestmentCategory)

    def test_brokerage_is_concrete(self):
        b = Brokerage()
        self.assertIsInstance(b, InvestmentCategory)

    def test_retirement_is_concrete(self):
        r = Retirement()
        self.assertIsInstance(r, InvestmentCategory)

    def test_base_class_is_abstract(self):
        self.assertTrue(issubclass(InvestmentCategory, ABC))


class TestInvestmentCategoryDefaults(unittest.TestCase):
    def test_default_amount_is_zero(self):
        for cls in (Savings, Brokerage, Retirement):
            self.assertAlmostEqual(cls().amount, 0.0)

    def test_default_cycle_is_monthly(self):
        for cls in (Savings, Brokerage, Retirement):
            self.assertEqual(cls().cycle, "monthly")

    def test_default_summary_label_is_none(self):
        for cls in (Savings, Brokerage, Retirement):
            self.assertIsNone(cls()._summary_label)

    def test_constructor_sets_amount_and_cycle(self):
        s = Savings(250.0, "weekly")
        self.assertAlmostEqual(s.amount, 250.0)
        self.assertEqual(s.cycle, "weekly")


class TestInvestmentCategoryKeys(unittest.TestCase):
    def test_savings_amount_key(self):
        self.assertEqual(Savings().amount_key, "savings_amount")

    def test_savings_cycle_key(self):
        self.assertEqual(Savings().cycle_key, "savings_cycle")

    def test_brokerage_amount_key(self):
        self.assertEqual(Brokerage().amount_key, "brokerage_amount")

    def test_brokerage_cycle_key(self):
        self.assertEqual(Brokerage().cycle_key, "brokerage_cycle")

    def test_retirement_amount_key(self):
        self.assertEqual(Retirement().amount_key, "retirement_amount")

    def test_retirement_cycle_key(self):
        self.assertEqual(Retirement().cycle_key, "retirement_cycle")

    def test_all_keys_are_unique(self):
        cats = [Savings(), Brokerage(), Retirement()]
        amount_keys = [c.amount_key for c in cats]
        cycle_keys  = [c.cycle_key  for c in cats]
        self.assertEqual(len(set(amount_keys)), 3)
        self.assertEqual(len(set(cycle_keys)),  3)


class TestToMonthlyMonthly(unittest.TestCase):
    def _assert_monthly(self, cls):
        cat = cls(120.0, "monthly")
        self.assertAlmostEqual(cat.to_monthly(), 120.0)

    def test_savings_monthly(self):    self._assert_monthly(Savings)
    def test_brokerage_monthly(self):  self._assert_monthly(Brokerage)
    def test_retirement_monthly(self): self._assert_monthly(Retirement)


class TestToMonthlyWeekly(unittest.TestCase):
    def _assert_weekly(self, cls):
        cat = cls(100.0, "weekly")
        self.assertAlmostEqual(cat.to_monthly(), 100.0 * 52 / 12)

    def test_savings_weekly(self):    self._assert_weekly(Savings)
    def test_brokerage_weekly(self):  self._assert_weekly(Brokerage)
    def test_retirement_weekly(self): self._assert_weekly(Retirement)


class TestToMonthlyDaily(unittest.TestCase):
    def _assert_daily(self, cls):
        cat = cls(100.0, "daily")
        self.assertAlmostEqual(cat.to_monthly(), 100.0 * 365 / 12)

    def test_savings_daily(self):    self._assert_daily(Savings)
    def test_brokerage_daily(self):  self._assert_daily(Brokerage)
    def test_retirement_daily(self): self._assert_daily(Retirement)


class TestToMonthlyZero(unittest.TestCase):
    def test_zero_amount_returns_zero_for_all_cycles(self):
        for cls in (Savings, Brokerage, Retirement):
            for cycle in ("daily", "weekly", "monthly"):
                self.assertAlmostEqual(cls(0.0, cycle).to_monthly(), 0.0)


class TestCategoryMetadata(unittest.TestCase):
    def test_all_have_label(self):
        for cls in (Savings, Brokerage, Retirement):
            self.assertTrue(cls.label)

    def test_labels_are_unique(self):
        labels = [cls.label for cls in (Savings, Brokerage, Retirement)]
        self.assertEqual(len(set(labels)), 3)

    def test_all_have_colors(self):
        for cls in (Savings, Brokerage, Retirement):
            self.assertTrue(cls.color.startswith("#"))
            self.assertTrue(cls.bar_color.startswith("#"))


if __name__ == "__main__":
    unittest.main()
