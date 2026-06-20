#!/usr/bin/env python3
"""
PDF Renamer GUI
Renames PDF files based on the NAME field found in their text content.
Packaged as a standalone Windows .exe — no Python installation required.
"""

import re
import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# ── PDF backend (bundled by PyInstaller) ─────────────────────────────────────
try:
    import pdfplumber as _pl
    _BACKEND = "pdfplumber"
except ImportError:
    try:
        import PyPDF2 as _p2
        _BACKEND = "PyPDF2"
    except ImportError:
        _BACKEND = None


def _extract_text(pdf_path: Path) -> str:
    if _BACKEND == "pdfplumber":
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                return "\n".join(p.extract_text() or "" for p in pdf.pages)
        except Exception:
            return ""
    elif _BACKEND == "PyPDF2":
        try:
            import PyPDF2
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception:
            return ""
    return ""


def _find_name(text: str):
    patterns = [
        r'NAME\s*[:\-]\s*([^\n\r]+)',
        r'Name\s*[:\-]\s*([^\n\r]+)',
        r'name\s*[:\-]\s*([^\n\r]+)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            if "UAN NO" in raw.upper():
                raw = raw.upper().split("UAN NO")[0].strip()
            clean = re.sub(r'[<>:"/\\|?*]', '', raw)
            clean = re.sub(r'\s+', ' ', clean).strip()
            if clean:
                return clean
    return None


def _safe_name(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:200]


# ── GUI ───────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    BG      = "#1e1e2e"
    FG      = "#cdd6f4"
    CARD    = "#313244"
    ACCENT  = "#89b4fa"
    OK      = "#a6e3a1"
    WARN    = "#f9e2af"
    ERR     = "#f38ba8"
    BTN     = "#45475a"
    DIM     = "#6c7086"

    def __init__(self):
        super().__init__()
        self.title("PDF Renamer")
        self.geometry("740x580")
        self.minsize(600, 480)
        self.configure(bg=self.BG)
        self._running = False
        self._build_ui()
        self._check_backend()

    # ── layout ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame",         background=self.BG)
        s.configure("TLabel",         background=self.BG,   foreground=self.FG)
        s.configure("TButton",        background=self.BTN,  foreground=self.FG,     padding=6)
        s.map("TButton",              background=[("active", self.ACCENT)])
        s.configure("Accent.TButton", background=self.ACCENT, foreground="#1e1e2e", padding=8)
        s.map("Accent.TButton",       background=[("active", "#74c7ec")])
        s.configure("TProgressbar",   troughcolor=self.CARD, background=self.ACCENT)

        ttk.Label(self, text="PDF Renamer", font=("Segoe UI", 17, "bold"),
                  foreground=self.ACCENT).pack(pady=(16, 0))
        ttk.Label(self, text="Batch-rename PDF files using the NAME field inside each document",
                  foreground=self.DIM).pack(pady=(2, 14))

        self._src = tk.StringVar()
        self._dst = tk.StringVar()
        self._folder_row("Source folder  (contains the PDFs to rename)",     self._src, self._pick_src)
        self._folder_row("Output folder  (renamed copies will be saved here)", self._dst, self._pick_dst)

        # Progress bar
        self._progress = ttk.Progressbar(self, mode="determinate")
        self._progress.pack(fill=tk.X, padx=16, pady=(8, 0))

        # Status
        self._status = tk.StringVar(value="Ready — select folders above, then click Start")
        ttk.Label(self, textvariable=self._status, foreground=self.DIM).pack(
            anchor=tk.W, padx=16, pady=(4, 0))

        # Buttons
        bf = ttk.Frame(self)
        bf.pack(fill=tk.X, padx=16, pady=8)
        self._btn_start = ttk.Button(bf, text="▶  Start Renaming",
                                     style="Accent.TButton", command=self._start)
        self._btn_start.pack(side=tk.LEFT)
        self._btn_cancel = ttk.Button(bf, text="⏹  Cancel",
                                      command=self._cancel, state=tk.DISABLED)
        self._btn_cancel.pack(side=tk.LEFT, padx=8)
        ttk.Button(bf, text="Clear Log", command=self._clear_log).pack(side=tk.RIGHT)

        # Log
        lf = tk.Frame(self, bg=self.CARD, padx=1, pady=1)
        lf.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        self._log = scrolledtext.ScrolledText(
            lf, state=tk.DISABLED, bg="#181825", fg=self.FG,
            font=("Consolas", 9), insertbackground=self.FG, relief=tk.FLAT, bd=0)
        self._log.pack(fill=tk.BOTH, expand=True)
        self._log.tag_config("ok",   foreground=self.OK)
        self._log.tag_config("skip", foreground=self.WARN)
        self._log.tag_config("err",  foreground=self.ERR)
        self._log.tag_config("info", foreground=self.ACCENT)
        self._log.tag_config("dim",  foreground=self.DIM)

    def _folder_row(self, label, var, cmd):
        outer = tk.Frame(self, bg=self.CARD, padx=10, pady=8)
        outer.pack(fill=tk.X, padx=16, pady=4)
        tk.Label(outer, text=label, bg=self.CARD, fg=self.DIM,
                 font=("Segoe UI", 8)).pack(anchor=tk.W)
        inner = tk.Frame(outer, bg=self.CARD)
        inner.pack(fill=tk.X, pady=(4, 0))
        tk.Entry(inner, textvariable=var, bg="#1e1e2e", fg=self.FG,
                 insertbackground=self.FG, relief=tk.FLAT, bd=0,
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        tk.Button(inner, text="Browse…", bg=self.BTN, fg=self.FG,
                  relief=tk.FLAT, activebackground=self.ACCENT,
                  command=cmd, padx=10, pady=4).pack(side=tk.LEFT, padx=(8, 0))

    # ── actions ──────────────────────────────────────────────────────────────
    def _pick_src(self):
        p = filedialog.askdirectory(title="Select Source Folder (PDFs to rename)")
        if p:
            self._src.set(p)

    def _pick_dst(self):
        p = filedialog.askdirectory(title="Select Output Folder")
        if p:
            self._dst.set(p)

    def _start(self):
        src, dst = self._src.get().strip(), self._dst.get().strip()
        if not src or not dst:
            messagebox.showwarning("PDF Renamer", "Please select both source and output folders.")
            return
        if not Path(src).is_dir():
            messagebox.showerror("PDF Renamer", f"Source folder not found:\n{src}")
            return
        self._running = True
        self._btn_start.config(state=tk.DISABLED)
        self._btn_cancel.config(state=tk.NORMAL)
        self._progress.config(value=0)
        threading.Thread(target=self._worker, args=(src, dst), daemon=True).start()

    def _cancel(self):
        self._running = False
        self._status.set("Cancelling…")

    def _write_log(self, msg, tag=""):
        self._log.config(state=tk.NORMAL)
        self._log.insert(tk.END, msg + "\n", tag)
        self._log.see(tk.END)
        self._log.config(state=tk.DISABLED)

    def _clear_log(self):
        self._log.config(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.config(state=tk.DISABLED)

    # ── worker thread ─────────────────────────────────────────────────────────
    def _worker(self, src_dir: str, dst_dir: str):
        src, dst = Path(src_dir), Path(dst_dir)
        try:
            dst.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._write_log(f"Cannot create output folder: {e}", "err")
            self._finish()
            return

        # collect unique PDFs (case-insensitive on Windows)
        seen, pdfs = set(), []
        for f in list(src.glob("*.pdf")) + list(src.glob("*.PDF")):
            key = f.resolve()
            if key not in seen:
                seen.add(key)
                pdfs.append(f)

        if not pdfs:
            self._write_log("No PDF files found in the source folder.", "skip")
            self._finish()
            return

        total = len(pdfs)
        self._write_log(f"Found {total} PDF file(s)  •  Output → {dst.resolve()}", "info")
        self._progress.config(maximum=total)

        renamed = errors = 0
        for i, pdf in enumerate(pdfs, 1):
            if not self._running:
                self._write_log("── Cancelled ──", "dim")
                break

            self._status.set(f"Processing {i}/{total}:  {pdf.name}")
            self._progress.config(value=i)
            self.update_idletasks()

            text = _extract_text(pdf)
            if not text:
                self._write_log(f"  SKIP  (no text extracted)    {pdf.name}", "skip")
                errors += 1
                continue

            name = _find_name(text)
            if not name:
                self._write_log(f"  SKIP  (NAME field not found)  {pdf.name}", "skip")
                errors += 1
                continue

            safe = _safe_name(name)
            out = dst / f"{safe}.pdf"
            n = 1
            while out.exists():
                out = dst / f"{safe}_{n}.pdf"
                n += 1

            try:
                shutil.copy2(pdf, out)
                self._write_log(f"  OK    {pdf.name}  →  {out.name}", "ok")
                renamed += 1
            except Exception as e:
                self._write_log(f"  ERR   {pdf.name}: {e}", "err")
                errors += 1

        self._write_log("─" * 60, "dim")
        self._write_log(f"  {renamed} renamed   {errors} skipped/errors", "info")
        if renamed:
            self._write_log(f"  Saved to: {dst.resolve()}", "info")
        self._finish(renamed, errors)

    def _finish(self, renamed=0, errors=0):
        self._running = False
        self._btn_start.config(state=tk.NORMAL)
        self._btn_cancel.config(state=tk.DISABLED)
        if renamed or errors:
            self._status.set(f"Done — {renamed} renamed, {errors} skipped")
        else:
            self._status.set("Ready — select folders above, then click Start")

    def _check_backend(self):
        if _BACKEND is None:
            messagebox.showerror(
                "PDF Renamer",
                "No PDF library found in this build.\n"
                "Please rebuild using build_windows.bat."
            )
            self._btn_start.config(state=tk.DISABLED)
        else:
            self._write_log(f"PDF backend: {_BACKEND}", "dim")


if __name__ == "__main__":
    App().mainloop()
