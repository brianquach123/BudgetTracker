import unittest
from constants import CYCLES, CARDS, CYCLE_TO_MONTHLY, monthly_equiv, to_monthly


class TestCycles(unittest.TestCase):
    def test_contains_all_expected_cycles(self):
        for cycle in ["monthly", "yearly", "quarterly", "weekly"]:
            self.assertIn(cycle, CYCLES)

    def test_cards_has_five_entries(self):
        self.assertEqual(len(CARDS), 5)

    def test_cards_contains_expected_names(self):
        for card in ["Discover It", "C1 Venture Mastercard", "C1 QuickSilver Mastercard (Virtual)",
                     "Sapphire Preferred Visa", "Prime Visa"]:
            self.assertIn(card, CARDS)


class TestCycleToMonthly(unittest.TestCase):
    def test_monthly_is_identity(self):
        self.assertAlmostEqual(CYCLE_TO_MONTHLY["monthly"](10.0), 10.0)

    def test_yearly_divides_by_twelve(self):
        self.assertAlmostEqual(CYCLE_TO_MONTHLY["yearly"](120.0), 10.0)

    def test_quarterly_divides_by_three(self):
        self.assertAlmostEqual(CYCLE_TO_MONTHLY["quarterly"](30.0), 10.0)

    def test_weekly_multiplies_by_52_over_12(self):
        self.assertAlmostEqual(CYCLE_TO_MONTHLY["weekly"](10.0), 10.0 * 52 / 12)

    def test_zero_cost_returns_zero(self):
        for fn in CYCLE_TO_MONTHLY.values():
            self.assertAlmostEqual(fn(0.0), 0.0)


class TestMonthlyEquiv(unittest.TestCase):
    def _sub(self, cycle, cost):
        return {"billing_cycle": cycle, "cost": cost}

    def test_monthly_subscription(self):
        self.assertAlmostEqual(monthly_equiv(self._sub("monthly", 9.99)), 9.99)

    def test_yearly_subscription(self):
        self.assertAlmostEqual(monthly_equiv(self._sub("yearly", 120.0)), 10.0)

    def test_quarterly_subscription(self):
        self.assertAlmostEqual(monthly_equiv(self._sub("quarterly", 30.0)), 10.0)

    def test_weekly_subscription(self):
        self.assertAlmostEqual(monthly_equiv(self._sub("weekly", 10.0)), 10.0 * 52 / 12)

    def test_zero_cost(self):
        self.assertAlmostEqual(monthly_equiv(self._sub("monthly", 0.0)), 0.0)


class TestToMonthly(unittest.TestCase):
    def test_monthly_is_identity(self):
        self.assertAlmostEqual(to_monthly(100.0, "monthly"), 100.0)

    def test_weekly_multiplies_by_52_over_12(self):
        self.assertAlmostEqual(to_monthly(100.0, "weekly"), 100.0 * 52 / 12)

    def test_daily_multiplies_by_365_over_12(self):
        self.assertAlmostEqual(to_monthly(100.0, "daily"), 100.0 * 365 / 12)

    def test_zero_amount_returns_zero(self):
        for cycle in ["daily", "weekly", "monthly"]:
            self.assertAlmostEqual(to_monthly(0.0, cycle), 0.0)


if __name__ == "__main__":
    unittest.main()
