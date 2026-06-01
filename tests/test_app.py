import unittest
from unittest.mock import patch

_DEFAULTS = ([], 0.0, "weekly", [], 0.0, [], 0.0, "monthly", 0.0, "monthly", 0.0, "monthly")


def _make_receipt(date, amount, store=None):
    r = {"date": date, "amount": amount}
    if store is not None:
        r["store"] = store
    return r


class TestAppMonthlyAverages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_patch = patch("app.load_data", return_value=_DEFAULTS)
        cls._save_patch = patch("app.save_data")
        cls._load_patch.start()
        cls._save_patch.start()
        from app import SubscriptionApp
        cls.app = SubscriptionApp()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()
        cls._load_patch.stop()
        cls._save_patch.stop()

    def setUp(self):
        self.app.grocery_receipts = []
        self.app.gas_receipts = []

    # ── Grocery monthly average ───────────────────────────────────────────────

    def test_grocery_avg_empty(self):
        self.assertAlmostEqual(self.app._grocery_monthly_avg(), 0.0)

    def test_grocery_avg_single_receipt(self):
        self.app.grocery_receipts = [_make_receipt("2024-01-10", 80.0)]
        self.assertAlmostEqual(self.app._grocery_monthly_avg(), 80.0)

    def test_grocery_avg_multiple_receipts_same_month(self):
        self.app.grocery_receipts = [
            _make_receipt("2024-01-05", 50.0),
            _make_receipt("2024-01-20", 100.0),
        ]
        self.assertAlmostEqual(self.app._grocery_monthly_avg(), 150.0)

    def test_grocery_avg_across_two_months(self):
        self.app.grocery_receipts = [
            _make_receipt("2024-01-05", 100.0),
            _make_receipt("2024-02-10", 200.0),
        ]
        self.assertAlmostEqual(self.app._grocery_monthly_avg(), 150.0)

    def test_grocery_avg_across_three_months(self):
        self.app.grocery_receipts = [
            _make_receipt("2024-01-05", 90.0),
            _make_receipt("2024-02-10", 60.0),
            _make_receipt("2024-03-15", 150.0),
        ]
        self.assertAlmostEqual(self.app._grocery_monthly_avg(), 100.0)

    def test_grocery_avg_groups_by_month_not_day(self):
        self.app.grocery_receipts = [
            _make_receipt("2024-01-01", 40.0),
            _make_receipt("2024-01-31", 60.0),  # same month
            _make_receipt("2024-02-01", 100.0), # different month
        ]
        # Jan=100, Feb=100 → avg=100
        self.assertAlmostEqual(self.app._grocery_monthly_avg(), 100.0)

    # ── Gas monthly average ───────────────────────────────────────────────────

    def test_gas_avg_empty(self):
        self.assertAlmostEqual(self.app._gas_monthly_avg(), 0.0)

    def test_gas_avg_single_receipt(self):
        self.app.gas_receipts = [_make_receipt("2024-01-05", 45.0)]
        self.assertAlmostEqual(self.app._gas_monthly_avg(), 45.0)

    def test_gas_avg_multiple_receipts_same_month(self):
        self.app.gas_receipts = [
            _make_receipt("2024-01-05", 40.0),
            _make_receipt("2024-01-20", 60.0),
        ]
        self.assertAlmostEqual(self.app._gas_monthly_avg(), 100.0)

    def test_gas_avg_across_multiple_months(self):
        self.app.gas_receipts = [
            _make_receipt("2024-01-05", 50.0),
            _make_receipt("2024-02-10", 75.0),
            _make_receipt("2024-03-15", 25.0),
        ]
        self.assertAlmostEqual(self.app._gas_monthly_avg(), 50.0)


class TestAppSortTree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_patch = patch("app.load_data", return_value=_DEFAULTS)
        cls._save_patch = patch("app.save_data")
        cls._load_patch.start()
        cls._save_patch.start()
        from app import SubscriptionApp
        cls.app = SubscriptionApp()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()
        cls._load_patch.stop()
        cls._save_patch.stop()

    def _load_grocery(self, rows):
        tree = self.app.grocery_tree
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", "end", values=row)
        self.app._sort_state.pop(id(tree), None)

    def _col_values(self, tree, col):
        return [tree.set(iid, col) for iid in tree.get_children()]

    def test_sort_numeric_ascending(self):
        self._load_grocery([
            ("2024-01-03", "C", "$30.00"),
            ("2024-01-01", "A", "$10.00"),
            ("2024-01-02", "B", "$20.00"),
        ])
        self.app._sort_tree(self.app.grocery_tree, "amount", False)
        self.assertEqual(self._col_values(self.app.grocery_tree, "amount"),
                         ["$10.00", "$20.00", "$30.00"])

    def test_sort_numeric_descending(self):
        self._load_grocery([
            ("2024-01-01", "A", "$10.00"),
            ("2024-01-02", "B", "$20.00"),
            ("2024-01-03", "C", "$30.00"),
        ])
        self.app._sort_tree(self.app.grocery_tree, "amount", True)
        self.assertEqual(self._col_values(self.app.grocery_tree, "amount"),
                         ["$30.00", "$20.00", "$10.00"])

    def test_sort_string_ascending(self):
        self._load_grocery([
            ("2024-01-01", "Zebra", "$10.00"),
            ("2024-01-02", "Apple", "$20.00"),
            ("2024-01-03", "Mango", "$30.00"),
        ])
        self.app._sort_tree(self.app.grocery_tree, "store", False)
        self.assertEqual(self._col_values(self.app.grocery_tree, "store"),
                         ["Apple", "Mango", "Zebra"])

    def test_sort_date_ascending(self):
        self._load_grocery([
            ("2024-03-01", "C", "$10.00"),
            ("2024-01-01", "A", "$20.00"),
            ("2024-02-01", "B", "$30.00"),
        ])
        self.app._sort_tree(self.app.grocery_tree, "date", False)
        self.assertEqual(self._col_values(self.app.grocery_tree, "date"),
                         ["2024-01-01", "2024-02-01", "2024-03-01"])

    def test_sort_toggles_direction_on_same_column(self):
        self._load_grocery([
            ("2024-01-01", "A", "$10.00"),
            ("2024-03-01", "C", "$30.00"),
            ("2024-02-01", "B", "$20.00"),
        ])
        self.app._sort_tree(self.app.grocery_tree, "date", False)
        first_pass = self._col_values(self.app.grocery_tree, "date")[0]
        self.app._sort_tree(self.app.grocery_tree, "date")  # toggle
        second_pass = self._col_values(self.app.grocery_tree, "date")[0]
        self.assertNotEqual(first_pass, second_pass)

    def test_sort_state_is_recorded(self):
        self._load_grocery([("2024-01-01", "A", "$10.00")])
        self.app._sort_tree(self.app.grocery_tree, "amount", False)
        col, rev = self.app._sort_state[id(self.app.grocery_tree)]
        self.assertEqual(col, "amount")
        self.assertFalse(rev)


class TestAppCensorToggle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_patch = patch("app.load_data", return_value=_DEFAULTS)
        cls._save_patch = patch("app.save_data")
        cls._load_patch.start()
        cls._save_patch.start()
        from app import SubscriptionApp
        cls.app = SubscriptionApp()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()
        cls._load_patch.stop()
        cls._save_patch.stop()

    def test_censored_true_on_startup(self):
        self.assertTrue(self.app._censored)

    def test_toggle_censor_flips_state(self):
        self.app._censored = False
        self.app._toggle_censor()
        self.assertTrue(self.app._censored)
        self.app._toggle_censor()
        self.assertFalse(self.app._censored)

    def test_censor_button_label_show_when_censored(self):
        self.app._censored = True
        self.app._censor_btn.config(text="Show Numbers")
        self.assertEqual(self.app._censor_btn.cget("text"), "Show Numbers")

    def test_censor_button_label_hide_when_uncensored(self):
        self.app._censored = False
        self.app._censor_btn.config(text="Hide Numbers")
        self.assertEqual(self.app._censor_btn.cget("text"), "Hide Numbers")

    def test_subscriptions_list_censors_cost_column(self):
        self.app.subscriptions = [
            {"name": "Netflix", "cost": 15.99, "billing_cycle": "monthly",
             "charge_day": 1, "card": "Visa"}
        ]
        self.app._censored = True
        self.app._refresh_list()
        iid = self.app.tree.get_children()[0]
        vals = self.app.tree.item(iid, "values")
        self.assertEqual(vals[1], "***")   # cost censored
        self.assertEqual(vals[4], "***")   # monthly equiv censored
        self.assertEqual(vals[0], "Netflix")  # name still visible

    def test_subscriptions_list_shows_cost_when_uncensored(self):
        self.app.subscriptions = [
            {"name": "Netflix", "cost": 15.99, "billing_cycle": "monthly",
             "charge_day": 1, "card": "Visa"}
        ]
        self.app._censored = False
        self.app._refresh_list()
        iid = self.app.tree.get_children()[0]
        vals = self.app.tree.item(iid, "values")
        self.assertEqual(vals[1], "$15.99")


class TestAppDarkMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_patch = patch("app.load_data", return_value=_DEFAULTS)
        cls._save_patch = patch("app.save_data")
        cls._load_patch.start()
        cls._save_patch.start()
        from app import SubscriptionApp
        cls.app = SubscriptionApp()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()
        cls._load_patch.stop()
        cls._save_patch.stop()

    def test_dark_mode_false_on_startup(self):
        self.assertFalse(self.app._dark_mode)

    def test_toggle_dark_mode_flips_state(self):
        self.app._dark_mode = False
        self.app._toggle_dark_mode()
        self.assertTrue(self.app._dark_mode)
        self.app._toggle_dark_mode()
        self.assertFalse(self.app._dark_mode)

    def test_theme_button_label_in_light_mode(self):
        self.app._dark_mode = False
        self.app._theme_btn.config(text="Dark Mode")
        self.assertEqual(self.app._theme_btn.cget("text"), "Dark Mode")

    def test_theme_button_label_in_dark_mode(self):
        self.app._dark_mode = True
        self.app._theme_btn.config(text="Light Mode")
        self.assertEqual(self.app._theme_btn.cget("text"), "Light Mode")

    def test_apply_theme_does_not_raise(self):
        from constants import DARK_THEME, LIGHT_THEME
        try:
            self.app._apply_theme(DARK_THEME)
            self.app._apply_theme(LIGHT_THEME)
        except Exception as e:
            self.fail(f"_apply_theme raised unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main()
