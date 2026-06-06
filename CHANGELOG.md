# Changelog

## [2.0.0] - 2026-06-06

### Added
- **Credit card inventory tab** — add, edit, and delete cards with network, last-4, limit, and APR fields
- **Card management** — full CRUD for stored payment cards
- **PDF export** — generate a multi-page PDF report of subscriptions and financial data via fpdf2
- **Auto dark mode** — UI theme automatically switches to dark after 9 PM
- **Data compression** — subscription data is now zlib-compressed before encryption (v2 file format); existing v1 data is migrated automatically on first load
- **PyInstaller packaging** — project ships with `BudgetTracker.spec` to build a standalone Windows `.exe`

### Fixed
- Sorting bug when updating cards

### Internal
- Added `.gitignore` entries for PyInstaller build artifacts (`dist/`, `build/`)
- Encrypted data file (`subscriptions.json`) is no longer tracked by git
