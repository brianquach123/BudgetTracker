# Budget and Subscription Tracker

A local, privacy-first personal finance tracker built with Python and Tkinter. All data is stored in a JSON file on your machine — nothing leaves your computer.

## Features

- **Paycheck** — log your biweekly after-tax income; all summary percentages are calculated against this
- **Rent** — weekly or monthly rent with a monthly equivalent in the summary
- **Subscriptions** — track name, cost, billing cycle, charge day, and credit card per subscription
- **Savings / Brokerage / Retirement** — log periodic investment contributions (daily, weekly, or monthly)
- **Grocery receipts** — log individual receipts with date and store; displays a monthly average
- **Gas receipts** — log fill-ups by date; displays a monthly average
- **Budget bar** — a colour-coded segmented bar showing how each expense category eats into your income
- **Monthly breakdown** — right-aligned summary with dollar amounts and percentage-of-income for every category
- **Censor toggle** — hide all sensitive numbers with a single click (on by default at startup)
- **Dark / Light mode** — toggle between themes
- **Sortable lists** — click any column header to sort; all receipt lists default to most-recent-first
- **Collapsible input forms** — all input panels start collapsed to keep the UI clean

## Project structure

```
BudgetTracker/
├── subscriptions.py      # Entry point
├── app.py                # SubscriptionApp — main Tk window and all UI logic
├── categories.py         # InvestmentCategory ABC + Savings, Brokerage, Retirement subclasses
├── constants.py          # Shared constants, cycle helpers, and theme palettes
├── data.py               # load_data / save_data — JSON persistence
├── widgets.py            # make_toggle_form — reusable collapsible form widget
└── tests/
    ├── test_app.py        # App logic: monthly averages, sort, censor, dark mode
    ├── test_categories.py # InvestmentCategory hierarchy and to_monthly calculations
    ├── test_constants.py  # Cycle conversions and helper functions
    └── test_data.py       # load_data / save_data round-trip and legacy format handling
```

## Requirements

- Python 3.8+ (Tkinter is included in the standard library)
- No third-party packages required

## Setup

```bash
# Create and activate a virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

## Running the app

```bash
python subscriptions.py
```

Or directly with the venv interpreter:

```bash
.\.venv\Scripts\python.exe subscriptions.py
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

## Data storage

Budget data is saved to `subscriptions.json` in the project directory. This file is listed in `.gitignore` and will never be committed — your financial data stays local.

## Colour coding

Each expense category has a consistent colour across the toggle-form header and the budget bar:

| Category | Colour |
|---|---|
| Paycheck / income | Green `#43a047` |
| Rent | Purple `#7b1fa2` |
| Subscriptions | Orange `#fb8c00` |
| Groceries | Blue `#1976d2` |
| Gas | Brown `#795548` |
| Savings | Light green `#a5d6a7` |
| Brokerage | Medium green `#43a047` |
| Retirement | Dark green `#1b5e20` |
