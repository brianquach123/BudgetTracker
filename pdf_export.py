import datetime
from tkinter.filedialog import asksaveasfilename

from fpdf import FPDF

from constants import monthly_equiv


def _compute_monthly_values(paycheck_biweekly, subscriptions, rent_amount,
                             rent_cycle, grocery_receipts, gas_receipts, investments):
    paycheck_monthly = paycheck_biweekly * 2
    subs_total = sum(monthly_equiv(s) for s in subscriptions)
    rent_monthly = rent_amount * 52 / 12 if rent_cycle == "weekly" else rent_amount

    if grocery_receipts:
        by_month = {}
        for r in grocery_receipts:
            by_month.setdefault(r["date"][:7], 0.0)
            by_month[r["date"][:7]] += r["amount"]
        grocery_monthly = sum(by_month.values()) / len(by_month)
        grocery_by_month = sorted(by_month.items())
    else:
        grocery_monthly = 0.0
        grocery_by_month = []

    if gas_receipts:
        by_month = {}
        for r in gas_receipts:
            by_month.setdefault(r["date"][:7], 0.0)
            by_month[r["date"][:7]] += r["amount"]
        gas_monthly = sum(by_month.values()) / len(by_month)
        gas_by_month = sorted(by_month.items())
    else:
        gas_monthly = 0.0
        gas_by_month = []

    investment_monthlies = [(cat, cat.to_monthly()) for cat in investments]
    inv_total = sum(m for _, m in investment_monthlies)
    combined = subs_total + rent_monthly + grocery_monthly + gas_monthly + inv_total
    leftover = paycheck_monthly - combined

    return {
        "paycheck_monthly": paycheck_monthly,
        "subs_total": subs_total,
        "rent_monthly": rent_monthly,
        "grocery_monthly": grocery_monthly,
        "grocery_by_month": grocery_by_month,
        "gas_monthly": gas_monthly,
        "gas_by_month": gas_by_month,
        "investment_monthlies": investment_monthlies,
        "combined": combined,
        "leftover": leftover,
        "over_budget": combined > paycheck_monthly,
    }


def _hex_to_rgb(hex_str):
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _draw_table(pdf, headers, col_widths, rows, header_fill=(66, 133, 244), x_start=None):
    if x_start is not None:
        pdf.set_x(x_start)
    x_origin = pdf.get_x()
    pdf.set_font("Helvetica", "B", 8)
    r, g, b = header_fill
    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    for header, w in zip(headers, col_widths):
        pdf.cell(w, 6, header, border=1, fill=True, align="C")
    pdf.ln()
    if x_start is not None:
        pdf.set_x(x_origin)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 8)
    for i, row in enumerate(rows):
        if i % 2 == 1:
            pdf.set_fill_color(245, 245, 245)
        else:
            pdf.set_fill_color(255, 255, 255)
        for cell, w in zip(row, col_widths):
            pdf.cell(w, 5, str(cell), border=1, fill=True, align="L")
        pdf.ln()
        if x_start is not None:
            pdf.set_x(x_origin)
    end_y = pdf.get_y()
    if x_start is None:
        pdf.ln(2)
    return end_y


def _draw_budget_bar(pdf, vals):
    BAR_WIDTH = 190.0
    BAR_HEIGHT = 6.0
    x_origin = pdf.get_x()
    y = pdf.get_y()

    paycheck = vals["paycheck_monthly"]
    over = vals["over_budget"]
    combined = vals["combined"]

    segments = [
        (vals["subs_total"],      "#e53935" if over else "#fb8c00"),
        (vals["rent_monthly"],    "#7b1fa2"),
        (vals["grocery_monthly"], "#1976d2"),
        (vals["gas_monthly"],     "#795548"),
    ]
    for cat, m in vals["investment_monthlies"]:
        segments.append((m, cat.bar_color))

    if paycheck > 0:
        scale = BAR_WIDTH / paycheck
    elif combined > 0:
        scale = BAR_WIDTH / combined
    else:
        pdf.set_fill_color(200, 200, 200)
        pdf.rect(x_origin, y, BAR_WIDTH, BAR_HEIGHT, style="F")
        pdf.ln(BAR_HEIGHT + 1)
        return

    pdf.set_fill_color(208, 208, 208)
    pdf.rect(x_origin, y, BAR_WIDTH, BAR_HEIGHT, style="F")

    x = x_origin
    right_edge = x_origin + BAR_WIDTH
    for amount, color in segments:
        seg_w = min(amount * scale, right_edge - x)
        if seg_w > 0:
            r, g, b = _hex_to_rgb(color)
            pdf.set_fill_color(r, g, b)
            pdf.rect(x, y, seg_w, BAR_HEIGHT, style="F")
            x += seg_w

    pdf.ln(BAR_HEIGHT + 1)


def _draw_bar_legend(pdf, vals):
    over = vals["over_budget"]
    legend_items = [
        ("#e53935" if over else "#fb8c00", "Subscriptions"),
        ("#7b1fa2", "Rent/Mortgage"),
        ("#1976d2", "Groceries"),
        ("#795548", "Gas"),
    ]
    for cat, _ in vals["investment_monthlies"]:
        legend_items.append((cat.bar_color, cat.label))

    swatch_w = 4.0
    swatch_h = 3.0
    gap = 1.5
    item_gap = 5.0
    y = pdf.get_y()
    x = pdf.get_x()

    pdf.set_font("Helvetica", "", 7)
    for color, label in legend_items:
        r, g, b = _hex_to_rgb(color)
        pdf.set_fill_color(r, g, b)
        pdf.rect(x, y, swatch_w, swatch_h, style="F")
        pdf.set_xy(x + swatch_w + gap, y)
        text_w = pdf.get_string_width(label) + 1
        pdf.cell(text_w, swatch_h, label)
        x += swatch_w + gap + text_w + item_gap

    pdf.ln(swatch_h + 3)


def _section_monthly_summary(pdf, vals):
    paycheck_monthly = vals["paycheck_monthly"]

    def pct(amount):
        if paycheck_monthly <= 0:
            return "N/A"
        return f"{amount / paycheck_monthly * 100:.1f}%"

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Monthly Budget Report", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Generated: {datetime.date.today().strftime('%B %d, %Y')}", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f"Gross Monthly Income:  ${paycheck_monthly:,.2f}", ln=True)
    pdf.ln(1)

    headers = ["Category", "Monthly Amount", "% of Income"]
    col_widths = [90.0, 55.0, 45.0]

    rows = [
        ["Subscriptions",   f"${vals['subs_total']:,.2f}",      pct(vals['subs_total'])],
        ["Rent / Mortgage", f"${vals['rent_monthly']:,.2f}",    pct(vals['rent_monthly'])],
        ["Groceries (avg)", f"${vals['grocery_monthly']:,.2f}", pct(vals['grocery_monthly'])],
        ["Gas (avg)",       f"${vals['gas_monthly']:,.2f}",     pct(vals['gas_monthly'])],
    ]
    for cat, m in vals["investment_monthlies"]:
        rows.append([cat.label, f"${m:,.2f}", pct(m)])
    rows.append(["TOTAL EXPENSES", f"${vals['combined']:,.2f}", pct(vals['combined'])])
    rows.append(["Leftover",       f"${vals['leftover']:,.2f}", pct(vals['leftover'])])

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Budget Breakdown (proportional to income)", ln=True)
    _draw_budget_bar(pdf, vals)
    _draw_bar_legend(pdf, vals)

    pdf.ln(1)
    _draw_table(pdf, headers, col_widths, rows)


def _draw_column_panel(pdf, x, start_y, half_w, col_w, title, subtitle, by_month, avg_label):
    """Draw a titled month/total table at an explicit (x, start_y). Returns the final y."""
    y = start_y
    # Title + subtitle on the same line
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "B", 10)
    title_text = title + ":"
    title_w = pdf.get_string_width(title_text) + 2
    pdf.cell(title_w, 7, title_text)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(half_w - title_w, 7, " " + subtitle)
    y += 7
    if by_month:
        # Table header
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(66, 133, 244)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(col_w[0], 6, "Month", border=1, fill=True, align="C")
        pdf.cell(col_w[1], 6, "Total Spent", border=1, fill=True, align="C")
        y += 6
        # Data rows
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 8)
        for i, (month, total) in enumerate(by_month):
            pdf.set_xy(x, y)
            pdf.set_fill_color(245, 245, 245) if i % 2 else pdf.set_fill_color(255, 255, 255)
            pdf.cell(col_w[0], 5, month, border=1, fill=True)
            pdf.cell(col_w[1], 5, f"${total:,.2f}", border=1, fill=True)
            y += 5
        # Avg line
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(sum(col_w), 5, avg_label)
        y += 5
    else:
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(half_w, 5, f"No {title.lower()} receipts recorded.")
        y += 5
    return y


def _section_granular_breakdown(pdf, vals, subscriptions, rent_amount, rent_cycle):
    paycheck_monthly = vals["paycheck_monthly"]

    def pct(amount):
        if paycheck_monthly <= 0:
            return "N/A"
        return f"{amount / paycheck_monthly * 100:.1f}%"

    def section_heading(label, amount):
        pdf.set_font("Helvetica", "B", 10)
        label_w = pdf.get_string_width(label + ":") + 2
        pdf.cell(label_w, 7, label + ":", ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 7, f" ${amount:,.2f}  ({pct(amount)})", ln=True)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Granular Breakdown", ln=True)
    pdf.ln(1)

    # Subscriptions
    section_heading("Subscriptions", vals["subs_total"])
    if subscriptions:
        headers = ["Name", "Cost", "Billing Cycle", "Card"]
        col_widths = [60.0, 28.0, 38.0, 64.0]
        rows = [
            [s["name"], f"${s['cost']:.2f}", s["billing_cycle"], s.get("card", "")]
            for s in subscriptions
        ]
        _draw_table(pdf, headers, col_widths, rows)
    else:
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 5, "No subscriptions configured.", ln=True)
        pdf.ln(2)

    # Rent / Mortgage
    section_heading("Rent / Mortgage", vals["rent_monthly"])
    if rent_amount > 0:
        headers = ["Amount", "Billing Cycle", "Monthly Equivalent"]
        col_widths = [63.0, 63.0, 64.0]
        rows = [[f"${rent_amount:.2f}", rent_cycle, f"${vals['rent_monthly']:,.2f}"]]
        _draw_table(pdf, headers, col_widths, rows)
    else:
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 5, "No rent / mortgage configured.", ln=True)
        pdf.ln(2)

    # Groceries and Gas — side by side, anchored to left and right margins
    HALF_W = 65.0
    LEFT_X = 10.0
    RIGHT_X = 200.0 - HALF_W
    COL_W = [28.0, 37.0]

    # Ensure both panels fit on the same page without an auto-page-break mid-draw.
    n_rows = max(len(vals["grocery_by_month"]), len(vals["gas_by_month"]))
    panel_height = 7 + (6 + n_rows * 5 + 5 if n_rows > 0 else 5)
    if pdf.get_y() + panel_height > pdf.h - pdf.b_margin:
        pdf.add_page()

    start_y = pdf.get_y()
    n_g = len(vals["grocery_by_month"])
    n_gas = len(vals["gas_by_month"])
    grocery_final_y = _draw_column_panel(
        pdf, LEFT_X, start_y, HALF_W, COL_W,
        title="Groceries",
        subtitle=f"${vals['grocery_monthly']:,.2f}  ({pct(vals['grocery_monthly'])})",
        by_month=vals["grocery_by_month"],
        avg_label=f"Avg: ${vals['grocery_monthly']:,.2f}  ({n_g} mo)",
    )
    gas_final_y = _draw_column_panel(
        pdf, RIGHT_X, start_y, HALF_W, COL_W,
        title="Gas",
        subtitle=f"${vals['gas_monthly']:,.2f}  ({pct(vals['gas_monthly'])})",
        by_month=vals["gas_by_month"],
        avg_label=f"Avg: ${vals['gas_monthly']:,.2f}  ({n_gas} mo)",
    )
    pdf.set_y(max(grocery_final_y, gas_final_y) + 3)

    # Investments
    inv_total = sum(m for _, m in vals["investment_monthlies"])
    section_heading("Investments", inv_total)
    headers = ["Category", "Amount", "Cycle", "Monthly Equivalent"]
    col_widths = [50.0, 38.0, 38.0, 64.0]
    rows = [
        [cat.label, f"${cat.amount:.2f}", cat.cycle, f"${m:,.2f}"]
        for cat, m in vals["investment_monthlies"]
    ]
    _draw_table(pdf, headers, col_widths, rows)


def _section_credit_card_inventory(pdf, cards, subscriptions):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Credit Card Inventory", ln=True)
    pdf.ln(1)

    by_card = {card: [] for card in cards}
    for sub in subscriptions:
        card = sub.get("card", "")
        if card in by_card:
            by_card[card].append(sub)

    for card in cards:
        subs_on_card = by_card[card]
        monthly_total = sum(monthly_equiv(s) for s in subs_on_card)

        pdf.set_font("Helvetica", "B", 10)
        card_label = card + ":"
        card_w = pdf.get_string_width(card_label) + 2
        pdf.cell(card_w, 7, card_label, ln=False)
        pdf.set_font("Helvetica", "", 9)
        if subs_on_card:
            n = len(subs_on_card)
            pdf.cell(0, 7,
                     f" {n} subscription{'s' if n != 1 else ''}  -  ${monthly_total:,.2f}/mo",
                     ln=True)
            headers = ["Name", "Cost", "Billing Cycle", "Monthly Equiv."]
            col_widths = [72.0, 28.0, 36.0, 54.0]
            rows = [
                [s["name"], f"${s['cost']:.2f}", s["billing_cycle"],
                 f"${monthly_equiv(s):,.2f}"]
                for s in subs_on_card
            ]
            _draw_table(pdf, headers, col_widths, rows)
        else:
            pdf.cell(0, 7, " No subscriptions", ln=True)
            pdf.ln(2)


def export_budget_pdf(paycheck_biweekly, subscriptions, rent_amount, rent_cycle,
                      grocery_receipts, gas_receipts, investments, cards):
    path = asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        initialfile=f"budget_{datetime.date.today().isoformat()}.pdf",
        title="Save Budget PDF",
    )
    if not path:
        return

    vals = _compute_monthly_values(
        paycheck_biweekly, subscriptions, rent_amount, rent_cycle,
        grocery_receipts, gas_receipts, investments,
    )

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=10, top=10, right=10)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    _section_monthly_summary(pdf, vals)
    _section_granular_breakdown(pdf, vals, subscriptions, rent_amount, rent_cycle)
    _section_credit_card_inventory(pdf, cards, subscriptions)

    pdf.output(path)
