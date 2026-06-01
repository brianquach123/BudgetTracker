import tkinter as tk
from tkinter import ttk


def make_toggle_form(parent, row, label, bg, fg, content_builder):
    """Collapsible form with a colored header bar. Starts collapsed."""
    outer = ttk.Frame(parent)
    outer.grid(row=row, column=0, sticky="ew", padx=(12, 6), pady=2)
    outer.columnconfigure(0, weight=1)

    header = tk.Frame(outer, bg=bg)
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(1, weight=1)

    content = ttk.Frame(outer, padding=8, relief="groove", borderwidth=1)
    content.columnconfigure(1, weight=1)
    content_builder(content)

    expanded = [False]
    btn = tk.Button(header, text="▶", bg=bg, fg=fg, activebackground=bg,
                    relief="flat", bd=0, width=2, font=("", 9, "bold"), cursor="hand2")
    btn.grid(row=0, column=0, padx=(4, 2), pady=3)
    tk.Label(header, text=label, bg=bg, fg=fg, font=("", 9, "bold")).grid(
        row=0, column=1, sticky="w", pady=3)

    def toggle(b=btn, c=content, e=expanded):
        if e[0]:
            c.grid_remove()
            b.config(text="▶")
        else:
            c.grid(row=1, column=0, sticky="ew")
            b.config(text="▼")
        e[0] = not e[0]

    btn.config(command=toggle)
    return content
