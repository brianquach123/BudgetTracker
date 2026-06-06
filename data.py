import base64
import json
import os
import sys
import zlib

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from constants import CARDS as _DEFAULT_CARDS

_PBKDF2_ITERATIONS = 480_000

# Set once by init_encryption(); used by every load_data / save_data call.
_fernet: "Fernet | None" = None
_salt: "bytes | None" = None


def _base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DATA_FILE = os.path.join(_base_dir(), "subscriptions.json")

_DEFAULTS = (
    [], 0.0, "weekly", [], 0.0, [], 0.0, "monthly", 0.0, "monthly", 0.0, "monthly",
    list(_DEFAULT_CARDS),
)

_DEFAULTS_DICT = {
    "subscriptions": [],
    "rent_amount": 0.0,
    "rent_cycle": "weekly",
    "grocery_receipts": [],
    "paycheck_biweekly": 0.0,
    "gas_receipts": [],
    "savings_amount": 0.0,
    "savings_cycle": "monthly",
    "brokerage_amount": 0.0,
    "brokerage_cycle": "monthly",
    "retirement_amount": 0.0,
    "retirement_cycle": "monthly",
    "cards": list(_DEFAULT_CARDS),
}


# ── Encryption helpers ────────────────────────────────────────────────────────

def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _is_plaintext(filepath: str) -> bool:
    try:
        with open(filepath, "r") as f:
            obj = json.load(f)
        return isinstance(obj, dict) and "v" not in obj
    except Exception:
        return False


def _write_encrypted(data_dict: dict) -> None:
    if _fernet is None or _salt is None:
        raise RuntimeError("Encryption not initialised — call init_encryption() first.")
    plaintext = zlib.compress(json.dumps(data_dict).encode("utf-8"), level=9)
    token = _fernet.encrypt(plaintext)
    envelope = {
        "v": 2,
        "salt": base64.b64encode(_salt).decode("ascii"),
        "data": token.decode("ascii"),
    }
    with open(DATA_FILE, "w") as f:
        json.dump(envelope, f)


def _ask_password(parent, title: str, prompt: str) -> "str | None":
    import tkinter as tk
    from tkinter import ttk

    result = [None]
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.focus_force()

    ttk.Label(dlg, text=prompt).pack(padx=24, pady=(16, 4))
    entry = ttk.Entry(dlg, show="*", width=32)
    entry.pack(padx=24, pady=4)
    entry.focus_set()

    def ok():
        result[0] = entry.get()
        dlg.destroy()

    def cancel():
        dlg.destroy()

    entry.bind("<Return>", lambda _: ok())
    btn_frame = ttk.Frame(dlg)
    btn_frame.pack(pady=(4, 16))
    ttk.Button(btn_frame, text="OK", command=ok, width=10).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Cancel", command=cancel, width=10).pack(side="left", padx=4)

    dlg.update_idletasks()
    sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
    dw, dh = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
    dlg.geometry(f"+{(sw - dw) // 2}+{(sh - dh) // 2}")

    dlg.wait_window()
    return result[0]


def _ask_new_password(parent) -> "str | None":
    from tkinter import messagebox

    while True:
        pw1 = _ask_password(parent, "Set Password", "Create a password for your data:")
        if pw1 is None:
            return None
        if not pw1:
            messagebox.showwarning("Password Required", "Password cannot be empty.",
                                   parent=parent)
            continue
        pw2 = _ask_password(parent, "Confirm Password", "Confirm your password:")
        if pw2 is None:
            return None
        if pw1 == pw2:
            return pw1
        messagebox.showwarning("Mismatch", "Passwords do not match. Please try again.",
                               parent=parent)


# ── Public entry point ────────────────────────────────────────────────────────

def init_encryption(parent_window) -> bool:
    """
    Set up the module-level Fernet key.  Must be called once before load_data / save_data.
    Returns True on success, False if the user cancels (app should exit).
    """
    global _fernet, _salt
    from tkinter import messagebox

    if not os.path.exists(DATA_FILE):
        # First run — ask user to create a password.
        pw = _ask_new_password(parent_window)
        if pw is None:
            return False
        _salt = os.urandom(16)
        _fernet = Fernet(_derive_key(pw, _salt))
        return True

    if _is_plaintext(DATA_FILE):
        # Existing unencrypted file — migrate.
        with open(DATA_FILE, "r") as f:
            existing = json.load(f)
        messagebox.showinfo(
            "Encrypt Your Data",
            "Your data file is not yet encrypted.\n"
            "Please set a password to secure it.",
            parent=parent_window,
        )
        pw = _ask_new_password(parent_window)
        if pw is None:
            return False
        _salt = os.urandom(16)
        _fernet = Fernet(_derive_key(pw, _salt))
        _write_encrypted(existing)
        return True

    # Encrypted file — prompt for password, retry on failure.
    while True:
        pw = _ask_password(parent_window, "Unlock Data", "Enter your password:")
        if pw is None:
            return False
        try:
            with open(DATA_FILE, "r") as f:
                envelope = json.load(f)
            salt = base64.b64decode(envelope["salt"])
            key = _derive_key(pw, salt)
            fernet = Fernet(key)
            raw = fernet.decrypt(envelope["data"].encode("ascii"))  # raises if wrong password
            _salt = salt
            _fernet = fernet
            if envelope.get("v", 1) < 2:
                _write_encrypted(json.loads(raw))
            return True
        except (InvalidToken, KeyError, Exception):
            messagebox.showerror("Wrong Password",
                                 "Incorrect password. Please try again.",
                                 parent=parent_window)


# ── Data access ───────────────────────────────────────────────────────────────

def load_data():
    if not os.path.exists(DATA_FILE):
        return _DEFAULTS
    if _fernet is None:
        raise RuntimeError("Encryption not initialised — call init_encryption() first.")
    with open(DATA_FILE, "r") as f:
        envelope = json.load(f)
    plaintext = _fernet.decrypt(envelope["data"].encode("ascii"))
    if envelope.get("v", 1) >= 2:
        plaintext = zlib.decompress(plaintext)
    raw = json.loads(plaintext)
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
        raw.get("cards", list(_DEFAULT_CARDS)),
    )


def save_data(subscriptions, rent_amount, rent_cycle, grocery_receipts,
              paycheck_biweekly, gas_receipts, savings_amount, savings_cycle,
              brokerage_amount, brokerage_cycle, retirement_amount, retirement_cycle,
              cards):
    _write_encrypted({
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
        "cards": cards,
    })
