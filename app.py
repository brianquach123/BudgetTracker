import datetime
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from categories import InvestmentCategory, Savings, Brokerage, Retirement
from constants import CYCLES, monthly_equiv, LIGHT_THEME, DARK_THEME
from data import load_data, save_data, init_encryption
from widgets import make_toggle_form
from pdf_export import export_budget_pdf

_OPEN_EYE_XBM = (
    "#define e_width 16\n#define e_height 10\n"
    "static unsigned char e_bits[] = {\n"
    "  0x00,0x00, 0xF0,0x0F, 0x0C,0x30, 0xC2,0x43,\n"
    "  0xC2,0x43, 0xC2,0x43, 0x0C,0x30, 0xF0,0x0F,\n"
    "  0x00,0x00, 0x00,0x00};"
)
_CLOSED_EYE_XBM = (
    "#define e_width 16\n#define e_height 10\n"
    "static unsigned char e_bits[] = {\n"
    "  0x00,0x00, 0x00,0x00, 0x00,0x00, 0xE0,0x07,\n"
    "  0xF8,0x1F, 0xE0,0x07, 0x00,0x00, 0x00,0x00,\n"
    "  0x00,0x00, 0x00,0x00};"
)


class SubscriptionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Budget and Subscription Tracker")
        self.resizable(True, True)
        self.minsize(1200, 500)
        self._dark_mode = datetime.datetime.now().hour >= 21
        self._build_eye_icons()
        toolbar = ttk.Frame(self, padding=(8, 4))
        toolbar.pack(side="top", fill="x")
        self._theme_btn = ttk.Button(toolbar,
                                     text="☀" if self._dark_mode else "🌙",
                                     command=self._toggle_dark_mode, width=3)
        self._theme_btn.pack(side="right")
        self._censor_btn = ttk.Button(toolbar, image=self._eye_closed_img,
                                      command=self._toggle_censor)
        self._censor_btn.pack(side="right", padx=(0, 6))
        self._pdf_btn = ttk.Button(toolbar, text="Export as PDF",
                                   command=self._export_pdf, width=14)
        self._pdf_btn.pack(side="right", padx=(0, 6))

        self.withdraw()
        if not init_encryption(self):
            self.destroy()
            sys.exit(0)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)
        self.tab1 = ttk.Frame(notebook)
        self.tab2 = ttk.Frame(notebook)
        notebook.add(self.tab1, text="Budget Tracker")
        notebook.add(self.tab2, text="Credit Card Inventory")
        self.tab1.columnconfigure(0, weight=1)
        self.tab1.columnconfigure(1, weight=1)
        self.tab1.columnconfigure(2, weight=1)
        self.tab1.rowconfigure(6, weight=1)
        (
            self.subscriptions, self.rent_amount, self.rent_cycle,
            self.grocery_receipts, self.paycheck_biweekly, self.gas_receipts,
            savings_amount, savings_cycle,
            brokerage_amount, brokerage_cycle,
            retirement_amount, retirement_cycle,
            self.cards,
        ) = load_data()
        self.investments: list[InvestmentCategory] = [
            Savings(savings_amount, savings_cycle),
            Brokerage(brokerage_amount, brokerage_cycle),
            Retirement(retirement_amount, retirement_cycle),
        ]
        self._sort_state = {}
        self._censored = True
        self._build_ui()
        self._apply_theme(DARK_THEME if self._dark_mode else LIGHT_THEME)
        self._refresh_list()
        self._refresh_groceries()
        self._refresh_gas()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = max(self.winfo_reqwidth(), self.winfo_width())
        h = max(self.winfo_reqheight(), self.winfo_height())
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")
        self.deiconify()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self):
        inv = {k: v for cat in self.investments
               for k, v in ((cat.amount_key, cat.amount), (cat.cycle_key, cat.cycle))}
        save_data(
            self.subscriptions, self.rent_amount, self.rent_cycle,
            self.grocery_receipts, self.paycheck_biweekly, self.gas_receipts,
            inv["savings_amount"], inv["savings_cycle"],
            inv["brokerage_amount"], inv["brokerage_cycle"],
            inv["retirement_amount"], inv["retirement_cycle"],
            self.cards,
        )

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_left_panel()
        self._build_grocery_panel()
        self._build_gas_panel()
        self._build_summary_panel()
        self._build_credit_card_inventory()

    def _build_left_panel(self):
        pad = {"padx": 8, "pady": 4}

        def _build_paycheck(f):
            self.paycheck_var = tk.StringVar(
                value=f"{self.paycheck_biweekly:.2f}" if self.paycheck_biweekly else ""
            )
            ttk.Label(f, text="Amount ($):").grid(row=0, column=0, sticky="e", **pad)
            ttk.Entry(f, textvariable=self.paycheck_var, width=12).grid(row=0, column=1, sticky="ew", **pad)
            ttk.Button(f, text="Save Paycheck", command=self._save_paycheck).grid(row=0, column=2, **pad)

        def _build_rent(f):
            self.rent_var = tk.StringVar(
                value=f"{self.rent_amount:.2f}" if self.rent_amount else ""
            )
            ttk.Label(f, text="Amount ($):").grid(row=0, column=0, sticky="e", **pad)
            ttk.Entry(f, textvariable=self.rent_var, width=12).grid(row=0, column=1, sticky="ew", **pad)
            ttk.Label(f, text="Cycle:").grid(row=0, column=2, sticky="e", **pad)
            self.rent_cycle_var = tk.StringVar(value=self.rent_cycle)
            ttk.Combobox(f, textvariable=self.rent_cycle_var,
                         values=["weekly", "monthly"], state="readonly", width=9
                         ).grid(row=0, column=3, sticky="w", **pad)
            ttk.Button(f, text="Save", command=self._save_rent).grid(row=0, column=4, **pad)

        for i, cat in enumerate(self.investments, start=2):
            def _build_investment(f, cat=cat):
                var_amount = tk.StringVar(value=f"{cat.amount:.2f}" if cat.amount else "")
                var_cycle  = tk.StringVar(value=cat.cycle)
                ttk.Label(f, text="Amount ($):").grid(row=0, column=0, sticky="e", **pad)
                ttk.Entry(f, textvariable=var_amount, width=12).grid(row=0, column=1, sticky="ew", **pad)
                ttk.Label(f, text="Cycle:").grid(row=0, column=2, sticky="e", **pad)
                ttk.Combobox(f, textvariable=var_cycle, values=["daily", "weekly", "monthly"],
                             state="readonly", width=9).grid(row=0, column=3, sticky="w", **pad)
                def _save_cat(c=cat, va=var_amount, vc=var_cycle):
                    raw = va.get().strip()
                    try:
                        value = float(raw)
                        if value < 0:
                            raise ValueError
                    except ValueError:
                        messagebox.showerror("Error", f"{c.label} amount must be a non-negative number.")
                        return
                    c.amount = value
                    c.cycle = vc.get()
                    self._save()
                    self._refresh_summary(sum(monthly_equiv(s) for s in self.subscriptions))
                ttk.Button(f, text="Save", command=_save_cat).grid(row=0, column=4, **pad)
            make_toggle_form(self.tab1, i, cat.label, cat.color, cat.fg_color, _build_investment)

        def _build_subscription(f):
            f.columnconfigure(1, weight=2)
            f.columnconfigure(3, weight=1)
            self.name_var = tk.StringVar()
            ttk.Label(f, text="Name:").grid(row=0, column=0, sticky="e", **pad)
            ttk.Entry(f, textvariable=self.name_var, width=22).grid(row=0, column=1, sticky="ew", **pad)
            self.cost_var = tk.StringVar()
            ttk.Label(f, text="Cost ($):").grid(row=0, column=2, sticky="e", **pad)
            ttk.Entry(f, textvariable=self.cost_var, width=10).grid(row=0, column=3, sticky="ew", **pad)
            self.cycle_var = tk.StringVar(value="monthly")
            ttk.Label(f, text="Billing cycle:").grid(row=1, column=0, sticky="e", **pad)
            ttk.Combobox(f, textvariable=self.cycle_var, values=CYCLES,
                         state="readonly", width=12).grid(row=1, column=1, sticky="w", **pad)
            self.day_var = tk.StringVar()
            ttk.Label(f, text="Charge day (1–31):").grid(row=1, column=2, sticky="e", **pad)
            ttk.Entry(f, textvariable=self.day_var, width=5).grid(row=1, column=3, sticky="w", **pad)
            self.card_var = tk.StringVar(value=self.cards[0] if self.cards else "")
            ttk.Label(f, text="Credit card:").grid(row=2, column=0, sticky="e", **pad)
            self._card_combobox = ttk.Combobox(f, textvariable=self.card_var,
                                               values=self.cards, state="readonly", width=20)
            self._card_combobox.grid(row=2, column=1, sticky="w", **pad)
            ttk.Button(f, text="Add Subscription", command=self._add).grid(
                row=3, column=0, columnspan=4, pady=(6, 2)
            )

        make_toggle_form(self.tab1, 0, "Paycheck (Biweekly, After Tax)", "#43a047", "white", _build_paycheck)
        make_toggle_form(self.tab1, 1, "Rent / Mortgage",   "#7b1fa2", "white", _build_rent)
        make_toggle_form(self.tab1, 5, "Subscription", "#fb8c00", "white", _build_subscription)

        list_frame = ttk.LabelFrame(self.tab1, text="Subscriptions", padding=8)
        list_frame.grid(row=6, column=0, sticky="nsew", padx=(12, 6), pady=4)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        cols = ("name", "cost", "cycle", "day", "monthly", "card")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=10, selectmode="browse")
        headings = {
            "name":    ("Name", 160),
            "cost":    ("Cost", 80),
            "cycle":   ("Cycle", 90),
            "day":     ("Day", 50),
            "monthly": ("Monthly Equiv.", 110),
            "card":    ("Credit Card", 160),
        }
        for col, (label, width) in headings.items():
            self.tree.heading(col, text=label, command=lambda c=col: self._sort_tree(self.tree, c))
            self.tree.column(col, width=width, anchor="center")
        self.tree.column("name", anchor="w")
        for col in ("cost", "cycle", "day", "monthly"):
            self.tree.column(col, stretch=False)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(6, 2))
        ttk.Button(btn_frame, text="Remove Selected", command=self._remove).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Change Card", command=self._change_card).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Manage Cards", command=self._manage_cards).pack(side="left", padx=4)

    def _build_grocery_panel(self):
        pad = {"padx": 8, "pady": 4}
        outer = ttk.Frame(self.tab1)
        outer.grid(row=0, column=1, rowspan=7, sticky="nsew", padx=6, pady=(12, 4))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        header = tk.Frame(outer, bg="#1976d2")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        tk.Label(header, text="Grocery Receipts", bg="#1976d2", fg="white",
                 font=("", 9, "bold")).grid(row=0, column=1, sticky="w", pady=3)

        form = ttk.Frame(outer, padding=(8, 4))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        exp = [False]
        btn = tk.Button(header, text="▶", bg="#1976d2", fg="white", activebackground="#1976d2",
                        relief="flat", bd=0, width=2, font=("", 9, "bold"), cursor="hand2")
        btn.grid(row=0, column=0, padx=(4, 2), pady=3)

        def _toggle(b=btn, f=form, e=exp):
            if e[0]:
                f.grid_remove(); b.config(text="▶")
            else:
                f.grid(row=1, column=0, sticky="ew"); b.config(text="▼")
            e[0] = not e[0]
        btn.config(command=_toggle)

        ttk.Label(form, text="Date:").grid(row=0, column=0, sticky="e", **pad)
        self.receipt_date_var = tk.StringVar(value=datetime.date.today().isoformat())
        ttk.Entry(form, textvariable=self.receipt_date_var, width=12).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Label(form, text="Store:").grid(row=0, column=2, sticky="e", **pad)
        self.receipt_store_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.receipt_store_var, width=14).grid(row=0, column=3, sticky="ew", **pad)
        ttk.Label(form, text="Amount ($):").grid(row=1, column=0, sticky="e", **pad)
        self.receipt_amount_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.receipt_amount_var, width=10).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(form, text="Add Receipt", command=self._add_receipt).grid(
            row=1, column=2, columnspan=2, **pad)

        grocery_cols = ("date", "store", "amount")
        self.grocery_tree = ttk.Treeview(outer, columns=grocery_cols, show="headings",
                                         height=6, selectmode="browse")
        self.grocery_tree.heading("date", text="Date",
                                   command=lambda: self._sort_tree(self.grocery_tree, "date"))
        self.grocery_tree.column("date", width=100, anchor="center")
        self.grocery_tree.heading("store", text="Store",
                                   command=lambda: self._sort_tree(self.grocery_tree, "store"))
        self.grocery_tree.column("store", width=130, anchor="w")
        self.grocery_tree.heading("amount", text="Amount",
                                   command=lambda: self._sort_tree(self.grocery_tree, "amount"))
        self.grocery_tree.column("amount", width=90, anchor="center")
        self.grocery_tree.column("date",   stretch=False)
        self.grocery_tree.column("amount", stretch=False)

        g_scroll = ttk.Scrollbar(outer, orient="vertical", command=self.grocery_tree.yview)
        self.grocery_tree.configure(yscrollcommand=g_scroll.set)
        self.grocery_tree.grid(row=2, column=0, sticky="nsew", padx=(8, 0), pady=4)
        g_scroll.grid(row=2, column=1, sticky="ns", pady=4)

        btn_frame = ttk.Frame(outer)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(2, 4))
        ttk.Button(btn_frame, text="Remove Selected", command=self._remove_receipt).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Change Store", command=self._change_store).pack(side="left", padx=4)

        self.grocery_avg_label = ttk.Label(outer, text="Average per receipt: $0.00   |   0 receipts logged")
        self.grocery_avg_label.grid(row=4, column=0, columnspan=2, pady=(0, 4))

    def _build_gas_panel(self):
        pad = {"padx": 8, "pady": 4}
        outer = ttk.Frame(self.tab1)
        outer.grid(row=0, column=2, rowspan=7, sticky="nsew", padx=(6, 12), pady=(12, 4))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        header = tk.Frame(outer, bg="#795548")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        tk.Label(header, text="Gas Receipts", bg="#795548", fg="white",
                 font=("", 9, "bold")).grid(row=0, column=1, sticky="w", pady=3)

        form = ttk.Frame(outer, padding=(8, 4))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        exp = [False]
        btn = tk.Button(header, text="▶", bg="#795548", fg="white", activebackground="#795548",
                        relief="flat", bd=0, width=2, font=("", 9, "bold"), cursor="hand2")
        btn.grid(row=0, column=0, padx=(4, 2), pady=3)

        def _toggle(b=btn, f=form, e=exp):
            if e[0]:
                f.grid_remove(); b.config(text="▶")
            else:
                f.grid(row=1, column=0, sticky="ew"); b.config(text="▼")
            e[0] = not e[0]
        btn.config(command=_toggle)

        ttk.Label(form, text="Date:").grid(row=0, column=0, sticky="e", **pad)
        self.gas_date_var = tk.StringVar(value=datetime.date.today().isoformat())
        ttk.Entry(form, textvariable=self.gas_date_var, width=12).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Label(form, text="Amount ($):").grid(row=0, column=2, sticky="e", **pad)
        self.gas_amount_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.gas_amount_var, width=10).grid(row=0, column=3, sticky="ew", **pad)
        ttk.Button(form, text="Add Receipt", command=self._add_gas).grid(
            row=1, column=0, columnspan=4, **pad)

        gas_cols = ("date", "amount")
        self.gas_tree = ttk.Treeview(outer, columns=gas_cols, show="headings",
                                     height=6, selectmode="browse")
        self.gas_tree.heading("date", text="Date",
                              command=lambda: self._sort_tree(self.gas_tree, "date"))
        self.gas_tree.column("date", width=130, anchor="center")
        self.gas_tree.heading("amount", text="Amount",
                              command=lambda: self._sort_tree(self.gas_tree, "amount"))
        self.gas_tree.column("amount", width=110, anchor="center")
        self.gas_tree.column("amount", stretch=False)

        gas_scroll = ttk.Scrollbar(outer, orient="vertical", command=self.gas_tree.yview)
        self.gas_tree.configure(yscrollcommand=gas_scroll.set)
        self.gas_tree.grid(row=2, column=0, sticky="nsew", padx=(8, 0), pady=4)
        gas_scroll.grid(row=2, column=1, sticky="ns", pady=4)

        ttk.Button(outer, text="Remove Selected", command=self._remove_gas).grid(
            row=3, column=0, columnspan=2, pady=(2, 4))
        self.gas_avg_label = ttk.Label(outer, text="Average per receipt: $0.00   |   0 receipts logged")
        self.gas_avg_label.grid(row=4, column=0, columnspan=2, pady=(0, 4))

    def _build_summary_panel(self):
        summary = ttk.Frame(self.tab1, padding=(12, 4, 12, 12))
        summary.grid(row=7, column=0, columnspan=3, sticky="ew")
        summary.columnconfigure(0, weight=1)
        summary.columnconfigure(1, weight=0)
        summary.columnconfigure(2, weight=2)

        ttk.Label(summary, text="Monthly paycheck equivalent:").grid(row=0, column=0, sticky="w")
        self.paycheck_label = ttk.Label(summary, text="$0.00 (100%)", anchor="e")
        self.paycheck_label.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Separator(summary, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=2)

        static_rows = [
            (2, "subs_label",    "Subscriptions monthly:"),
            (3, "rent_label",    "Rent / Mortgage monthly:"),
            (4, "grocery_label", "Grocery monthly average:"),
            (5, "gas_label",     "Gas monthly average:"),
        ]
        for row, attr, desc in static_rows:
            ttk.Label(summary, text=desc).grid(row=row, column=0, sticky="w")
            lbl = ttk.Label(summary, text="$0.00 (—)", anchor="e")
            lbl.grid(row=row, column=1, sticky="ew", padx=(8, 0))
            setattr(self, attr, lbl)

        for row, cat in enumerate(self.investments, start=6):
            ttk.Label(summary, text=f"{cat.label} monthly:").grid(row=row, column=0, sticky="w")
            lbl = ttk.Label(summary, text="$0.00 (—)", anchor="e")
            lbl.grid(row=row, column=1, sticky="ew", padx=(8, 0))
            cat._summary_label = lbl

        self.budget_canvas = tk.Canvas(summary, height=72, highlightthickness=0)
        self.budget_canvas.grid(row=2, column=2, rowspan=7, sticky="ew", pady=2, padx=(12, 0))
        self.budget_canvas.bind("<Configure>", lambda _: self._draw_budget_bars())

        ttk.Separator(summary, orient="horizontal").grid(
            row=9, column=0, columnspan=3, sticky="ew", pady=2)
        ttk.Label(summary, text="Combined monthly total:",
                  font=("", 11, "bold")).grid(row=10, column=0, sticky="w")
        self.combined_label = ttk.Label(summary, text="$0.00 (—)",
                                        font=("", 11, "bold"), anchor="e")
        self.combined_label.grid(row=10, column=1, sticky="ew", padx=(8, 0))
        self.leftover_label = ttk.Label(summary, text="Leftover: $0.00 (—)",
                                        font=("", 11, "bold"), anchor="e")
        self.leftover_label.grid(row=10, column=2, sticky="ew", padx=(12, 0))

    def _build_credit_card_inventory(self):
        self.tab2.columnconfigure(0, weight=1)
        self.tab2.rowconfigure(1, weight=1)

        # ── Input form ────────────────────────────────────────────────────────
        form = ttk.LabelFrame(self.tab2, text="Add Card", padding=8)
        form.grid(row=0, column=0, sticky="ew", padx=20, pady=(12, 8))
        form.columnconfigure(0, weight=1)

        self._inv_name_var = tk.StringVar()
        inv_entry = ttk.Entry(form, textvariable=self._inv_name_var, width=40)
        inv_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        inv_entry.bind("<Return>", lambda _: self._add_inventory_card())
        ttk.Button(form, text="Add", command=self._add_inventory_card).grid(row=0, column=1)

        # ── Card list ─────────────────────────────────────────────────────────
        list_frame = ttk.LabelFrame(self.tab2, text="Cards", padding=8)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 12))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._inv_tree = ttk.Treeview(list_frame, columns=("name",),
                                      show="headings", selectmode="browse")
        self._inv_tree.heading("name", text="Card Name",
                               command=lambda: self._sort_tree(self._inv_tree, "name"))
        self._inv_tree.column("name", anchor="w", stretch=True)

        inv_scroll = ttk.Scrollbar(list_frame, orient="vertical",
                                   command=self._inv_tree.yview)
        self._inv_tree.configure(yscrollcommand=inv_scroll.set)
        self._inv_tree.grid(row=0, column=0, sticky="nsew")
        inv_scroll.grid(row=0, column=1, sticky="ns")

        ttk.Button(list_frame, text="Remove Selected",
                   command=self._remove_inventory_card).grid(
            row=1, column=0, columnspan=2, pady=(6, 0))

        self._refresh_inventory()

    # ── Credit Card Inventory ─────────────────────────────────────────────────

    def _refresh_inventory(self):
        for iid in self._inv_tree.get_children():
            self._inv_tree.delete(iid)
        for i, card in enumerate(self.cards):
            self._inv_tree.insert("", "end", iid=str(i), values=(card,))

    def _add_inventory_card(self):
        name = self._inv_name_var.get().strip()
        if not name:
            return
        if name in self.cards:
            messagebox.showerror("Error", "That card already exists.")
            return
        self.cards.append(name)
        self._save()
        self._card_combobox.config(values=self.cards)
        self._inv_name_var.set("")
        self._refresh_inventory()

    def _remove_inventory_card(self):
        selected = self._inv_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a card to remove.")
            return
        idx = int(selected[0])
        self.cards.pop(idx)
        self._save()
        self._card_combobox.config(values=self.cards)
        self._refresh_inventory()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _save_paycheck(self):
        raw = self.paycheck_var.get().strip()
        try:
            value = float(raw)
            if value < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Paycheck amount must be a non-negative number.")
            return
        self.paycheck_biweekly = value
        self._save()
        self._refresh_summary(sum(monthly_equiv(s) for s in self.subscriptions))

    def _save_rent(self):
        raw = self.rent_var.get().strip()
        try:
            value = float(raw)
            if value < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Rent must be a non-negative number.")
            return
        self.rent_amount = value
        self.rent_cycle = self.rent_cycle_var.get()
        self._save()
        self._refresh_summary(sum(monthly_equiv(s) for s in self.subscriptions))

    def _add(self):
        name = self.name_var.get().strip()
        cost_raw = self.cost_var.get().strip()
        cycle = self.cycle_var.get()
        day_raw = self.day_var.get().strip()
        card = self.card_var.get()
        if not name:
            messagebox.showerror("Error", "Name is required.")
            return
        try:
            cost = float(cost_raw)
            if cost <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Cost must be a positive number.")
            return
        try:
            day = int(day_raw)
            if not 1 <= day <= 31:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Charge day must be a whole number between 1 and 31.")
            return
        self.subscriptions.append(
            {"name": name, "cost": cost, "billing_cycle": cycle, "charge_day": day, "card": card}
        )
        self._save()
        self._refresh_list()
        self.name_var.set("")
        self.cost_var.set("")
        self.day_var.set("")

    def _remove(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a subscription to remove.")
            return
        idx = int(selected[0])
        sub = self.subscriptions[idx]
        if messagebox.askyesno("Confirm", f"Remove '{sub['name']}'?"):
            self.subscriptions.pop(idx)
            self._save()
            self._refresh_list()

    def _change_card(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a subscription to update.")
            return
        idx = int(selected[0])
        sub = self.subscriptions[idx]
        dialog = tk.Toplevel(self)
        dialog.title("Change Credit Card")
        dialog.resizable(False, False)
        dialog.grab_set()
        ttk.Label(dialog, text=f"Subscription: {sub['name']}").grid(
            row=0, column=0, columnspan=2, padx=12, pady=(12, 4))
        ttk.Label(dialog, text="Credit card:").grid(row=1, column=0, sticky="e", padx=8, pady=4)
        card_var = tk.StringVar(value=sub.get("card", self.cards[0] if self.cards else ""))
        ttk.Combobox(dialog, textvariable=card_var, values=self.cards,
                     state="readonly", width=18).grid(row=1, column=1, padx=8, pady=4)

        def _apply():
            self.subscriptions[idx]["card"] = card_var.get()
            self._save()
            self._refresh_list()
            dialog.destroy()

        ttk.Button(dialog, text="Update", command=_apply).grid(
            row=2, column=0, columnspan=2, pady=(8, 12))

    def _manage_cards(self):
        dialog = tk.Toplevel(self)
        dialog.title("Manage Credit Cards")
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        listbox = tk.Listbox(frame, width=38, height=8, selectmode="browse",
                             exportselection=False)
        for card in self.cards:
            listbox.insert("end", card)
        listbox.grid(row=0, column=0, columnspan=2, pady=(0, 8))

        new_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=new_var, width=30)
        entry.grid(row=1, column=0, padx=(0, 4), pady=(0, 4))
        entry.focus()

        def _add():
            name = new_var.get().strip()
            if not name:
                return
            if name in self.cards:
                messagebox.showerror("Error", "That card already exists.", parent=dialog)
                return
            self.cards.append(name)
            listbox.insert("end", name)
            self._card_combobox.config(values=self.cards)
            new_var.set("")
            self._save()
            self._refresh_inventory()

        def _remove():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            self.cards.pop(idx)
            listbox.delete(idx)
            self._card_combobox.config(values=self.cards)
            self._save()
            self._refresh_inventory()

        dialog.bind("<Return>", lambda _: _add())
        ttk.Button(frame, text="Add", command=_add).grid(row=1, column=1, pady=(0, 4))
        ttk.Button(frame, text="Remove Selected", command=_remove).grid(
            row=2, column=0, columnspan=2, pady=(4, 0))

    def _add_receipt(self):
        date_raw = self.receipt_date_var.get().strip()
        store = self.receipt_store_var.get().strip()
        amount_raw = self.receipt_amount_var.get().strip()
        try:
            datetime.date.fromisoformat(date_raw)
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
            return
        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Amount must be a positive number.")
            return
        self.grocery_receipts.append({"date": date_raw, "store": store, "amount": amount})
        self._save()
        self._refresh_groceries()
        self.receipt_store_var.set("")
        self.receipt_amount_var.set("")
        self.receipt_date_var.set(datetime.date.today().isoformat())

    def _remove_receipt(self):
        selected = self.grocery_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a receipt to remove.")
            return
        idx = int(selected[0])
        self.grocery_receipts.pop(idx)
        self._save()
        self._refresh_groceries()

    def _change_store(self):
        selected = self.grocery_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a receipt to update.")
            return
        idx = int(selected[0])
        receipt = self.grocery_receipts[idx]
        dialog = tk.Toplevel(self)
        dialog.title("Change Store")
        dialog.resizable(False, False)
        dialog.grab_set()
        ttk.Label(dialog, text=f"Receipt: {receipt['date']}  ${receipt['amount']:.2f}").grid(
            row=0, column=0, columnspan=2, padx=12, pady=(12, 4))
        ttk.Label(dialog, text="Store:").grid(row=1, column=0, sticky="e", padx=8, pady=4)
        store_var = tk.StringVar(value=receipt.get("store", ""))
        store_entry = ttk.Entry(dialog, textvariable=store_var, width=22)
        store_entry.grid(row=1, column=1, padx=8, pady=4)
        store_entry.focus()

        def _apply():
            self.grocery_receipts[idx]["store"] = store_var.get().strip()
            self._save()
            self._refresh_groceries()
            dialog.destroy()

        dialog.bind("<Return>", lambda _: _apply())
        ttk.Button(dialog, text="Update", command=_apply).grid(
            row=2, column=0, columnspan=2, pady=(8, 12))

    def _add_gas(self):
        date_raw = self.gas_date_var.get().strip()
        amount_raw = self.gas_amount_var.get().strip()
        try:
            datetime.date.fromisoformat(date_raw)
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
            return
        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Amount must be a positive number.")
            return
        self.gas_receipts.append({"date": date_raw, "amount": amount})
        self._save()
        self._refresh_gas()
        self.gas_amount_var.set("")
        self.gas_date_var.set(datetime.date.today().isoformat())

    def _remove_gas(self):
        selected = self.gas_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a receipt to remove.")
            return
        idx = int(selected[0])
        self.gas_receipts.pop(idx)
        self._save()
        self._refresh_gas()

    def _toggle_censor(self):
        self._censored = not self._censored
        self._censor_btn.config(
            image=self._eye_open_img if not self._censored else self._eye_closed_img
        )
        self._refresh_list()

    def _export_pdf(self):
        export_budget_pdf(
            self.paycheck_biweekly, self.subscriptions,
            self.rent_amount, self.rent_cycle,
            self.grocery_receipts, self.gas_receipts,
            self.investments,
            self.cards,
        )

    def _build_eye_icons(self):
        fg = "white" if self._dark_mode else "#000000"
        self._eye_open_img   = tk.BitmapImage(data=_OPEN_EYE_XBM,   foreground=fg)
        self._eye_closed_img = tk.BitmapImage(data=_CLOSED_EYE_XBM, foreground=fg)

    def _toggle_dark_mode(self):
        self._dark_mode = not self._dark_mode
        self._theme_btn.config(text="☀" if self._dark_mode else "🌙")
        self._apply_theme(DARK_THEME if self._dark_mode else LIGHT_THEME)
        self._build_eye_icons()
        self._censor_btn.config(
            image=self._eye_open_img if not self._censored else self._eye_closed_img
        )

    def _apply_theme(self, c):
        self.configure(bg=c["bg"])
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".",
            background=c["bg"], foreground=c["fg"],
            troughcolor=c["bg"], bordercolor=c["bg"])
        style.configure("TFrame",      background=c["bg"])
        style.configure("TLabel",      background=c["bg"], foreground=c["fg"])
        style.configure("TLabelframe", background=c["bg"], bordercolor=c["heading_bg"])
        style.configure("TLabelframe.Label", background=c["bg"], foreground=c["fg"])
        style.configure("TButton",
            background=c["heading_bg"], foreground=c["fg"], bordercolor=c["heading_bg"])
        style.map("TButton",
            background=[("active", c["select_bg"]), ("pressed", c["select_bg"])],
            foreground=[("active", c["select_fg"]), ("pressed", c["select_fg"])])
        style.configure("TEntry",
            fieldbackground=c["entry_bg"], foreground=c["fg"],
            insertcolor=c["fg"], bordercolor=c["heading_bg"])
        style.configure("TCombobox",
            fieldbackground=c["entry_bg"], foreground=c["fg"],
            selectbackground=c["select_bg"], selectforeground=c["select_fg"],
            bordercolor=c["heading_bg"])
        style.map("TCombobox",
            fieldbackground=[("readonly", c["entry_bg"])],
            foreground=[("readonly", c["fg"])],
            selectbackground=[("readonly", c["select_bg"])])
        style.configure("Treeview",
            background=c["tree_bg"], foreground=c["fg"],
            fieldbackground=c["tree_bg"],
            selectbackground=c["select_bg"], selectforeground=c["select_fg"])
        style.configure("Treeview.Heading",
            background=c["heading_bg"], foreground=c["heading_fg"],
            bordercolor=c["heading_bg"])
        style.map("Treeview.Heading",
            background=[("active", c["select_bg"])],
            foreground=[("active", c["select_fg"])])
        style.configure("TSeparator", background=c["heading_bg"])
        style.configure("TScrollbar",
            background=c["heading_bg"], troughcolor=c["bg"],
            bordercolor=c["bg"], arrowcolor=c["fg"])
        style.configure("TNotebook", background=c["bg"])
        style.configure("TNotebook.Tab",
            background=c["heading_bg"], foreground=c["fg"],
            padding=(10, 4))
        style.map("TNotebook.Tab",
            background=[("selected", c["select_bg"]), ("active", c["heading_bg"])],
            foreground=[("selected", c["select_fg"]), ("active", c["fg"])])
        # update canvas background if already created
        if hasattr(self, "budget_canvas"):
            self.budget_canvas.configure(bg=c["canvas_bg"])
            self._draw_budget_bars()

    # ── Sorting ───────────────────────────────────────────────────────────────

    def _sort_tree(self, tree, col, reverse=None):
        key = id(tree)
        if reverse is None:
            _, prev_rev = self._sort_state.get(key, (col, False))
            reverse = not prev_rev if self._sort_state.get(key, (None,))[0] == col else False
        items = [(tree.set(iid, col), iid) for iid in tree.get_children("")]
        try:
            items.sort(key=lambda t: float(t[0].lstrip("$").replace(",", "")), reverse=reverse)
        except ValueError:
            items.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for i, (_, iid) in enumerate(items):
            tree.move(iid, "", i)
        self._sort_state[key] = (col, reverse)

    def _apply_sort(self, tree, default_col, default_reverse=False):
        col, rev = self._sort_state.get(id(tree), (default_col, default_reverse))
        self._sort_tree(tree, col, rev)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _grocery_monthly_avg(self):
        if not self.grocery_receipts:
            return 0.0
        by_month = {}
        for r in self.grocery_receipts:
            by_month.setdefault(r["date"][:7], 0.0)
            by_month[r["date"][:7]] += r["amount"]
        return sum(by_month.values()) / len(by_month)

    def _gas_monthly_avg(self):
        if not self.gas_receipts:
            return 0.0
        by_month = {}
        for r in self.gas_receipts:
            by_month.setdefault(r["date"][:7], 0.0)
            by_month[r["date"][:7]] += r["amount"]
        return sum(by_month.values()) / len(by_month)

    def _refresh_groceries(self):
        for row in self.grocery_tree.get_children():
            self.grocery_tree.delete(row)
        for i, r in enumerate(self.grocery_receipts):
            self.grocery_tree.insert("", "end", iid=str(i),
                values=(r["date"], r.get("store", ""), f"${r['amount']:.2f}"))
        self._apply_sort(self.grocery_tree, "date", True)
        n = len(self.grocery_receipts)
        avg = sum(r["amount"] for r in self.grocery_receipts) / n if n else 0.0
        self.grocery_avg_label.config(
            text=f"Average per receipt: ${avg:.2f}   |   {n} receipt{'s' if n != 1 else ''} logged")
        self._refresh_summary(sum(monthly_equiv(s) for s in self.subscriptions))

    def _refresh_gas(self):
        for row in self.gas_tree.get_children():
            self.gas_tree.delete(row)
        for i, r in enumerate(self.gas_receipts):
            self.gas_tree.insert("", "end", iid=str(i), values=(r["date"], f"${r['amount']:.2f}"))
        self._apply_sort(self.gas_tree, "date", True)
        n = len(self.gas_receipts)
        avg = sum(r["amount"] for r in self.gas_receipts) / n if n else 0.0
        self.gas_avg_label.config(
            text=f"Average per receipt: ${avg:.2f}   |   {n} receipt{'s' if n != 1 else ''} logged")
        self._refresh_summary(sum(monthly_equiv(s) for s in self.subscriptions))

    def _refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        subs_total = 0.0
        for i, sub in enumerate(self.subscriptions):
            equiv = monthly_equiv(sub)
            subs_total += equiv
            self.tree.insert("", "end", iid=str(i), values=(
                sub["name"], f"${sub['cost']:.2f}", sub["billing_cycle"],
                sub["charge_day"], f"${equiv:.2f}", sub.get("card", ""),
            ))
        if id(self.tree) in self._sort_state:
            col, rev = self._sort_state[id(self.tree)]
            self._sort_tree(self.tree, col, rev)
        self._refresh_summary(subs_total)
        if self._censored:
            for iid in self.tree.get_children():
                vals = list(self.tree.item(iid, "values"))
                vals[1] = "***"
                vals[4] = "***"
                self.tree.item(iid, values=vals)

    def _refresh_summary(self, subs_total):
        paycheck_monthly = self.paycheck_biweekly * 2
        rent_monthly = (
            self.rent_amount * 52 / 12 if self.rent_cycle == "weekly" else self.rent_amount
        )
        grocery_monthly = self._grocery_monthly_avg()
        gas_monthly = self._gas_monthly_avg()
        investment_monthlies = [cat.to_monthly() for cat in self.investments]
        combined = (subs_total + rent_monthly + grocery_monthly + gas_monthly
                    + sum(investment_monthlies))
        leftover = paycheck_monthly - combined

        def pct(amount):
            if paycheck_monthly <= 0:
                return "—"
            return f"{amount / paycheck_monthly * 100:.1f}%"

        def val(amount, pct_str, prefix=""):
            if self._censored:
                return f"{prefix}***"
            return f"{prefix}${amount:.2f} ({pct_str})"

        self.paycheck_label.config(text=val(paycheck_monthly, "100%"))
        self.subs_label.config(text=val(subs_total, pct(subs_total)))
        self.rent_label.config(text=val(rent_monthly, pct(rent_monthly)))
        g_pct = "" if self._censored else f" ({pct(grocery_monthly)})"
        self.grocery_label.config(text=f"${grocery_monthly:.2f}{g_pct}")
        gas_pct = "" if self._censored else f" ({pct(gas_monthly)})"
        self.gas_label.config(text=f"${gas_monthly:.2f}{gas_pct}")
        for cat, m in zip(self.investments, investment_monthlies):
            cat._summary_label.config(text=val(m, pct(m)))
        self.combined_label.config(text=val(combined, pct(combined)))
        self.leftover_label.config(text=val(leftover, pct(leftover), prefix="Leftover: "))
        self._draw_budget_bars()

    # ── Budget Bar ────────────────────────────────────────────────────────────

    def _draw_budget_bars(self):
        c = self.budget_canvas
        c.delete("all")
        w = c.winfo_width()
        if w <= 1:
            return

        paycheck_monthly = self.paycheck_biweekly * 2
        subs_total = sum(monthly_equiv(s) for s in self.subscriptions)
        rent_monthly = (
            self.rent_amount * 52 / 12 if self.rent_cycle == "weekly" else self.rent_amount
        )
        grocery_m = self._grocery_monthly_avg()
        gas_m     = self._gas_monthly_avg()
        investment_segments = [(cat.to_monthly(), cat.bar_color) for cat in self.investments]
        combined = (subs_total + rent_monthly + grocery_m + gas_m
                    + sum(m for m, _ in investment_segments))

        bar_h = 26
        pad_x = 4; pad_y = 4; gap = 8
        y0 = pad_y + bar_h + gap
        y1 = y0 + bar_h
        avail = w - 2 * pad_x

        if self._censored:
            c.create_rectangle(pad_x, pad_y, w - pad_x, pad_y + bar_h, fill="#222222", outline="")
            c.create_text(w / 2, pad_y + bar_h / 2, text="Income  ***",
                          fill="#555555", font=("", 9, "bold"))
            c.create_rectangle(pad_x, y0, w - pad_x, y1, fill="#222222", outline="")
            c.create_text(w / 2, y0 + bar_h / 2, text="Expenses  ***",
                          fill="#555555", font=("", 9, "bold"))
            return

        c.create_rectangle(pad_x, pad_y, w - pad_x, pad_y + bar_h, fill="#43a047", outline="")
        c.create_text(w / 2, pad_y + bar_h / 2,
                      text=f"Income  ${paycheck_monthly:,.2f}/mo",
                      fill="white", font=("", 9, "bold"))

        over = combined > paycheck_monthly
        scale = (avail / paycheck_monthly if paycheck_monthly > 0
                 else avail / combined if combined > 0 else 0)
        c.create_rectangle(pad_x, y0, pad_x + avail, y1, fill="#d0d0d0", outline="")

        expense_segments = [
            (subs_total,   "#e53935" if over else "#fb8c00"),
            (rent_monthly, "#7b1fa2"),
            (grocery_m,    "#1976d2"),
            (gas_m,        "#795548"),
        ]

        x = pad_x
        right_edge = pad_x + avail
        for amount, color in expense_segments:
            seg_w = min(amount * scale, right_edge - x)
            if seg_w > 0:
                c.create_rectangle(x, y0, x + seg_w, y1, fill=color, outline="")
                x += seg_w

        expense_group_end = x

        for amount, color in investment_segments:
            seg_w = min(amount * scale, right_edge - x)
            if seg_w > 0:
                c.create_rectangle(x, y0, x + seg_w, y1, fill=color, outline="")
                x += seg_w

        investment_group_end = x

        expense_total = subs_total + rent_monthly + grocery_m + gas_m
        investment_total = sum(m for m, _ in investment_segments)
        exp_pct = round(expense_total / paycheck_monthly * 100) if paycheck_monthly > 0 else 0
        inv_pct = round(investment_total / paycheck_monthly * 100) if paycheck_monthly > 0 else 0

        expense_group_width = expense_group_end - pad_x
        if expense_group_width > 0:
            c.create_text(pad_x + expense_group_width / 2, y0 + bar_h / 2,
                          text=f"Expenses ({exp_pct}%)", fill="white", font=("", 9, "bold"))

        investment_group_width = investment_group_end - expense_group_end
        if investment_segments and investment_total > 0 and investment_group_width > 0:
            c.create_text(expense_group_end + investment_group_width / 2, y0 + bar_h / 2,
                          text=f"Growth ({inv_pct}%)", fill="white", font=("", 9, "bold"))
