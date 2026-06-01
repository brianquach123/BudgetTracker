from abc import ABC, abstractmethod


class InvestmentCategory(ABC):
    label: str
    color: str      # toggle-header background
    fg_color: str   # toggle-header foreground
    bar_color: str  # budget-bar segment color

    def __init__(self, amount: float = 0.0, cycle: str = "monthly"):
        self.amount = amount
        self.cycle = cycle
        self._summary_label = None  # attached by _build_summary_panel

    def to_monthly(self) -> float:
        return {
            "daily":   self.amount * 365 / 12,
            "weekly":  self.amount * 52 / 12,
            "monthly": self.amount,
        }[self.cycle]

    @property
    @abstractmethod
    def amount_key(self) -> str: ...

    @property
    @abstractmethod
    def cycle_key(self) -> str: ...


class Savings(InvestmentCategory):
    label = "Savings"
    color = "#a5d6a7"
    fg_color = "#1a1a1a"
    bar_color = "#a5d6a7"

    @property
    def amount_key(self) -> str:
        return "savings_amount"

    @property
    def cycle_key(self) -> str:
        return "savings_cycle"


class Brokerage(InvestmentCategory):
    label = "Brokerage"
    color = "#43a047"
    fg_color = "white"
    bar_color = "#43a047"

    @property
    def amount_key(self) -> str:
        return "brokerage_amount"

    @property
    def cycle_key(self) -> str:
        return "brokerage_cycle"


class Retirement(InvestmentCategory):
    label = "Retirement"
    color = "#1b5e20"
    fg_color = "white"
    bar_color = "#1b5e20"

    @property
    def amount_key(self) -> str:
        return "retirement_amount"

    @property
    def cycle_key(self) -> str:
        return "retirement_cycle"
