# Budget and Subscription Tracker

A local, privacy-first personal finance tracker built with Python and Tkinter. All data is stored encrypted on your machine and nothing is ever transmitted over a network.

## Overview

The app provides a single-window interface with two tabs. The **Budget Tracker** tab covers income, recurring expenses, investment contributions, grocery and gas spending, and a real-time visual budget breakdown. The **Credit Card Inventory** tab maintains a list of your payment cards, each of which can be assigned to subscriptions.

On every launch the app prompts for a password before any data is loaded or displayed. Once authenticated, numbers are hidden by default and can be revealed with the **Show Numbers** button. After 9 PM the interface automatically starts in dark mode.

---

## Features

### Income and Expenses

* **Paycheck** — log your biweekly take-home pay. Every dollar amount and percentage in the summary is calculated relative to the derived monthly figure (biweekly × 2).
* **Rent / Mortgage** — enter a weekly or monthly amount. The summary always converts it to a monthly equivalent.
* **Subscriptions** — track name, cost, billing cycle (weekly, monthly, quarterly, or yearly), charge day, and assigned credit card. The list is sortable by any column.
* **Savings / Brokerage / Retirement** — log periodic investment contributions with daily, weekly, or monthly cycles. Each converts to a monthly equivalent for the summary.
* **Grocery receipts** — log individual trips with a date and store name. The summary shows a rolling monthly average derived by grouping receipts into calendar months and averaging across those months.
* **Gas receipts** — log fill-ups by date. Uses the same monthly averaging logic as groceries.

### Budget Summary and Visualisation

* **Budget bar** — a proportional colour-coded bar that compares total monthly expenses against monthly income. Each expense category occupies a segment sized relative to income. If expenses exceed income, the subscriptions segment turns red.
* **Monthly breakdown** — a right-aligned panel listing every category with its monthly dollar amount and percentage of income.
* **Colour coding** — consistent colours are used across toggle-form headers and the budget bar:

| Category | Colour |
|---|---|
| Income | Green `#43a047` |
| Rent / Mortgage | Purple `#7b1fa2` |
| Subscriptions | Orange `#fb8c00` (red `#e53935` when over budget) |
| Groceries | Blue `#1976d2` |
| Gas | Brown `#795548` |
| Savings | Light green `#a5d6a7` |
| Brokerage | Medium green `#43a047` |
| Retirement | Dark green `#1b5e20` |

### Credit Card Inventory

The second tab maintains a master list of your payment cards. Any card in this list can be assigned to a subscription. Cards can be added, removed, and sorted. The PDF export includes a dedicated credit card page that groups each card with the subscriptions assigned to it.

### PDF Export

Clicking **Export as PDF** opens a save dialog and generates a single-page A4 report containing:

* A proportional budget bar with a colour legend
* A summary table showing the monthly amount and percentage of income for every category
* A granular breakdown section with a subscriptions table, rent details, per-month grocery and gas totals with averages, and an investments table
* A second page listing each credit card alongside the subscriptions assigned to it

### Interface

* **Show / Hide Numbers** — toggles visibility of all dollar amounts and percentages. Numbers are hidden on every startup.
* **Dark / Light mode** — toggles between a light and dark theme. Automatically starts in dark mode after 9 PM based on the local system clock.
* **Sortable lists** — every column header in every list can be clicked to sort ascending or descending. Receipt lists default to most-recent-first.
* **Collapsible input forms** — all data-entry panels start collapsed so the interface stays uncluttered.
* **Centred startup** — both the password prompt and the main window open centred on the screen regardless of resolution or monitor size.

---

## Security

### Encryption at Rest

All data is encrypted before being written to disk using **Fernet** symmetric encryption from the `cryptography` library. Fernet uses AES-128-CBC with PKCS7 padding and authenticates every message with HMAC-SHA256, so any tampering or corruption is detected on load.

### Key Derivation

The encryption key is never stored anywhere. It is derived at runtime from your password using **PBKDF2HMAC with SHA-256** and a randomly generated 16-byte salt. The iteration count is set to **480,000**, in line with the OWASP 2023 recommendation for PBKDF2-SHA256. A different random salt is generated the first time a password is set, so two installations protected by the same password will still produce different keys.

### File Format

The data file is a JSON envelope with three fields:

```json
{
  "v": 2,
  "salt": "<base64-encoded 16-byte salt>",
  "data": "<Fernet token>"
}
```

The `v` field is a format version number used to handle migrations transparently. The salt is not secret and must be stored alongside the ciphertext so the key can be re-derived on the next launch. The Fernet token contains the nonce, ciphertext, and HMAC as a single self-contained base64 string.

### Compression

Before encrypting, the JSON payload is compressed with **zlib at level 9**. Compression runs before encryption so that the ciphertext reveals no structural patterns. The `v` field in the envelope distinguishes compressed files (v2) from earlier uncompressed files (v1); if a v1 file is opened it is automatically rewritten in v2 format after the password is verified.

### Password Handling

* On first launch (no data file present), the app prompts you to create a password and confirm it before anything else happens.
* If an unencrypted data file is found from a previous version of the app, a one-time migration prompts you to set a password and immediately rewrites the file encrypted.
* On every subsequent launch, the password is required to open the app. An incorrect password shows an error and allows another attempt. Cancelling exits the app.
* The derived key is held in memory only for the duration of the session and is never written to disk.

### Portability

Because the key is derived entirely from the password and the salt (which travels inside the data file), the encrypted file is fully portable. You can commit `subscriptions.json` to a private repository, pull it on another machine, and unlock it with the same password. No machine-specific secrets are involved.

---

## Project Structure

```
BudgetTracker/
├── subscriptions.py      # Entry point
├── app.py                # SubscriptionApp — main Tk window and all UI logic
├── categories.py         # InvestmentCategory ABC + Savings, Brokerage, Retirement subclasses
├── constants.py          # Shared constants, cycle helpers, and theme palettes
├── data.py               # Encryption, key derivation, load_data / save_data
├── pdf_export.py         # PDF generation logic (fpdf2)
├── widgets.py            # make_toggle_form — reusable collapsible form widget
├── requirements.txt      # Third-party dependencies
└── tests/
    ├── test_app.py        # App logic: monthly averages, sort, censor, dark mode
    ├── test_categories.py # InvestmentCategory hierarchy and to_monthly calculations
    ├── test_constants.py  # Cycle conversions and helper functions
    └── test_data.py       # load_data / save_data round-trip and legacy format handling
```

---

## Requirements

* Python 3.8 or later (Tkinter is included in the standard library)
* `cryptography` — Fernet encryption and PBKDF2 key derivation
* `fpdf2` — PDF generation

Install all dependencies with:

```
pip install -r requirements.txt
```

---

## Setup

```bash
python -m venv .venv
```

**Windows**

```bash
.\.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the App

```bash
python subscriptions.py
```

---

## Running the Tests

```bash
python -m unittest discover -s tests -v
```

---

## Data Storage

The data file `subscriptions.json` lives in the project directory. It contains only the encrypted, compressed envelope described above. Even if the file is accessed by another program or committed to version control, its contents are unreadable without the password.
