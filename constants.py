__version__ = "2.0.0"

CYCLES = ["monthly", "yearly", "quarterly", "weekly"]

LIGHT_THEME = {
    "bg":         "#f0f0f0",
    "fg":         "#000000",
    "entry_bg":   "#ffffff",
    "select_bg":  "#0078d4",
    "select_fg":  "#ffffff",
    "tree_bg":    "#ffffff",
    "heading_bg": "#e0e0e0",
    "heading_fg": "#000000",
    "canvas_bg":  "#f0f0f0",
}

DARK_THEME = {
    "bg":         "#1e1e1e",
    "fg":         "#d4d4d4",
    "entry_bg":   "#3c3c3c",
    "select_bg":  "#264f78",
    "select_fg":  "#ffffff",
    "tree_bg":    "#252526",
    "heading_bg": "#2d2d30",
    "heading_fg": "#cccccc",
    "canvas_bg":  "#1e1e1e",
}

CARDS = ["Discover It", "C1 Venture Mastercard", "C1 QuickSilver Mastercard (Virtual)", "Sapphire Preferred Visa", "Prime Visa"]

CYCLE_TO_MONTHLY = {
    "monthly": lambda cost: cost,
    "yearly": lambda cost: cost / 12,
    "quarterly": lambda cost: cost / 3,
    "weekly": lambda cost: cost * 52 / 12,
}


def monthly_equiv(sub):
    return CYCLE_TO_MONTHLY[sub["billing_cycle"]](sub["cost"])


def to_monthly(amount, cycle):
    return {"daily": amount * 365 / 12, "weekly": amount * 52 / 12, "monthly": amount}[cycle]
