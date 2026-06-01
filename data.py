import json
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subscriptions.json")

_DEFAULTS = [], 0.0, "weekly", [], 0.0, [], 0.0, "monthly", 0.0, "monthly", 0.0, "monthly"


def load_data():
    if not os.path.exists(DATA_FILE):
        return _DEFAULTS
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        return _DEFAULTS
    rent = raw.get("rent_amount", raw.get("rent_weekly", 0.0))
    return (
        raw.get("subscriptions", []),
        rent,
        raw.get("rent_cycle", "weekly"),
        raw.get("grocery_receipts", []),
        raw.get("paycheck_biweekly", 0.0),
        raw.get("gas_receipts", []),
        raw.get("savings_amount", 0.0),
        raw.get("savings_cycle", "monthly"),
        raw.get("brokerage_amount", 0.0),
        raw.get("brokerage_cycle", "monthly"),
        raw.get("retirement_amount", 0.0),
        raw.get("retirement_cycle", "monthly"),
    )


def save_data(subscriptions, rent_amount, rent_cycle, grocery_receipts,
              paycheck_biweekly, gas_receipts, savings_amount, savings_cycle,
              brokerage_amount, brokerage_cycle, retirement_amount, retirement_cycle):
    with open(DATA_FILE, "w") as f:
        json.dump(
            {
                "subscriptions": subscriptions,
                "rent_amount": rent_amount,
                "rent_cycle": rent_cycle,
                "grocery_receipts": grocery_receipts,
                "paycheck_biweekly": paycheck_biweekly,
                "gas_receipts": gas_receipts,
                "savings_amount": savings_amount,
                "savings_cycle": savings_cycle,
                "brokerage_amount": brokerage_amount,
                "brokerage_cycle": brokerage_cycle,
                "retirement_amount": retirement_amount,
                "retirement_cycle": retirement_cycle,
            },
            f,
            indent=2,
        )
