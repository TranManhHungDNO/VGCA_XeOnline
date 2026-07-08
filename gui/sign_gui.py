import os
import re
import glob
import shutil
import tempfile
import threading
import webbrowser
import sys
from typing import Optional, List, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk
import fitz  # PyMuPDF

from core.models import SignPlacement
from core.config_service import load_config, save_config
from core.pkcs11_reader import parse_certs
from core.convert_service import convert_to_pdf
from core.pdf_sign_service import sign_one_pdf


def resource_path(relative_path):
    """Lấy đường dẫn tài nguyên khi chạy source hoặc PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # sign_gui.py nằm trong gui/ → lên 1 cấp về project root
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        )
    return os.path.join(base_path, relative_path)




# =====================
# CONFIG
# =====================
from version import __version__
APP_TITLE = f"VGCA Token Signing Tool v{__version__}"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".vgca_sign_config.json")
SUPPORTED_INPUT_EXT = {".doc", ".docx", ".xls", ".xlsx", ".pdf"}
SUPPORTED_PNG_EXT = {".png"}
CORNER_HIT = 10

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BIT4ID_IMG = resource_path("bit4id.png")
SAFENET_IMG = resource_path("safenet.png")
ICON_ICO = resource_path("vgca.ico")
ICON_PNG = resource_path("vgca.png")

SAFENET_URL = "https://knowledge.digicert.com/general-information/how-to-download-safenet-authentication-client"
BIT4ID_URL = "https://suport.aoc.cat/en-US/article/?servei=tcat&id=KA-06990_manual-de-bit4id-per-a-linux"

CA_KEYWORDS = [
    "rootca", "root ca", "ca phục vụ", "ban cơ yếu",
    "ca g2", "ca g1", "vnpt-ca", "viettel-ca",
    "intermediate", "issuing ca",
]

# =====================
# PKCS11 PRIORITY
# =====================

# Ưu tiên theo yêu cầu:
# 1) Bit4id
# 2) SafeNet eToken
# 3) Scan tiếp các lib khác
PRIORITY_PKCS11 = [
    # Bit4id
    "/usr/lib/libbit4ipki.so",
    "/usr/lib/x86_64-linux-gnu/libbit4ipki.so",
    "/usr/local/lib/libbit4ipki.so",

    "/usr/lib/libbit4xpki.so",
    "/usr/lib/x86_64-linux-gnu/libbit4xpki.so",
    "/usr/local/lib/libbit4xpki.so",

    "/usr/lib/libbit4p11.so",
    "/usr/lib/x86_64-linux-gnu/libbit4p11.so",
    "/usr/local/lib/libbit4p11.so",

    # SafeNet
    "/usr/lib/libeTPkcs11.so",
    "/usr/lib/x86_64-linux-gnu/libeTPkcs11.so",
    "/usr/local/lib/libeTPkcs11.so",
]

FALLBACK_PKCS11 = [
    # SafeNet / eToken / IDPrime
    "/usr/lib/libeToken.so",
    "/usr/lib/x86_64-linux-gnu/libeToken.so",
    "/usr/local/lib/libeToken.so",

    "/usr/lib/libIDPrimePKCS11.so",
    "/usr/lib/x86_64-linux-gnu/libIDPrimePKCS11.so",
    "/usr/local/lib/libIDPrimePKCS11.so",

    # OpenSC
    "/usr/lib/opensc-pkcs11.so",
    "/usr/lib/x86_64-linux-gnu/opensc-pkcs11.so",
    "/usr/local/lib/opensc-pkcs11.so",
]

GLOB_PATTERNS = [
    "libbit4*.so",
    "libeTPkcs11*.so",
    "libeToken*.so",
    "libIDPrimePKCS11*.so",
    "opensc-pkcs11*.so",
    "*pkcs11*.so",
]

SEARCH_DIRS = [
    "/usr/lib",
    "/usr/lib64",
    "/usr/lib/x86_64-linux-gnu",
    "/usr/local/lib",
    "/lib",
    "/lib64",
    "/lib/x86_64-linux-gnu",
]

BOX_COLORS = {
    "signature": "#00aa55",
    "doc_no": "#1976d2",
    "day": "#ef6c00",
    "month": "#8e24aa",
    "year": "#c62828",
}

BOX_LABELS = {
    "signature": "Chữ ký",
    "doc_no": "Số VB",
    "day": "Ngày",
    "month": "Tháng",
    "year": "Năm",
}

BOX_DEFAULT_SIZE = {
    "signature": (220.0, 90.0),
    "doc_no": (180.0, 32.0),
    "day": (45.0, 32.0),
    "month": (45.0, 32.0),
    "year": (70.0, 32.0),
}

LEFT_PANEL_WIDTH = 500


# =====================
# POPUPS
# =====================
def _set_icon(win):
    try:
        if os.path.exists(ICON_PNG):
            win.iconphoto(True, tk.PhotoImage(file=ICON_PNG))
    except Exception:
        pass


def show_cert_detail(parent, cert: dict):
    win = tk.Toplevel(parent)
    win.title("Thông tin Certificate")
    win.resizable(False, False)
    win.grab_set()
    _set_icon(win)

    pw, ph = 520, 340
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{pw}x{ph}+{(sw - pw) // 2}+{(sh - ph) // 2}")

    tk.Label(win, text="🔐 Thông tin Certificate", font=("Arial", 13, "bold")).pack(pady=(16, 8))

    frm = tk.Frame(win, padx=20)
    frm.pack(fill="x")

    rows = [
        ("Người ký (CN):", cert.get("cn", "")),
        ("Tổ chức:", cert.get("org", "")),
        ("Email:", cert.get("email", "")),
        ("Token:", cert.get("token", "")),
        ("Slot:", str(cert.get("slot", ""))),
        ("Serial:", str(cert.get("serial", cert.get("token_serial", "")))),
        ("Label:", cert.get("label", "")),
        ("ID:", str(cert.get("id", ""))),
        ("CKA_ID:", str(cert.get("cka_id", ""))),
        ("Module:", cert.get("module", cert.get("pkcs11_lib", ""))),
    ]

    for i, (lbl, val) in enumerate(rows):
        tk.Label(frm, text=lbl, font=("Arial", 10, "bold"), anchor="w", width=18).grid(
            row=i, column=0, sticky="w", pady=3
        )
        tk.Label(frm, text=val or "(trống)", fg="#333", anchor="w", wraplength=300, justify="left").grid(
            row=i, column=1, sticky="w", pady=3
        )

    tk.Button(win, text="✅ Đóng", command=win.destroy, width=14).pack(pady=14)


def show_driver_suggestion(parent):
    win = tk.Toplevel(parent)
    win.title("Cài driver USB Token")
    win.resizable(False, False)
    win.grab_set()
    _set_icon(win)

    pw, ph = 560, 440
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{pw}x{ph}+{(sw - pw) // 2}+{(sh - ph) // 2}")

    tk.Label(win, text="❌ Chưa phát hiện driver USB Token", font=("Arial", 13, "bold"), fg="#c0392b").pack(
        pady=(16, 4)
    )
    tk.Label(
        win,
        text="Vui lòng chọn đúng loại USB Token và tải driver tương ứng.\n"
        "Sau khi cài xong -> cắm token -> nhấn 'Scan Token'.",
        justify="center",
        fg="#555",
    ).pack(pady=(0, 10))

    container = tk.Frame(win)
    container.pack(pady=6)

    f1 = tk.LabelFrame(container, text="Bit4id (VGCA)", padx=14, pady=10)
    f1.pack(side="left", padx=18)
    if os.path.exists(BIT4ID_IMG):
        try:
            img1 = Image.open(BIT4ID_IMG).resize((130, 86), Image.LANCZOS)
            img1_tk = ImageTk.PhotoImage(img1)
            lbl = tk.Label(f1, image=img1_tk)
            lbl.image = img1_tk
            lbl.pack(pady=(0, 8))
        except Exception:
            pass
    tk.Button(
        f1,
        text="📥 Tải driver Bit4id",
        command=lambda: webbrowser.open(BIT4ID_URL),
        bg="#2980b9",
        fg="white",
        font=("Arial", 10, "bold"),
        width=18,
    ).pack()

    f2 = tk.LabelFrame(container, text="SafeNet / eToken", padx=14, pady=10)
    f2.pack(side="left", padx=18)
    if os.path.exists(SAFENET_IMG):
        try:
            img2 = Image.open(SAFENET_IMG).resize((130, 86), Image.LANCZOS)
            img2_tk = ImageTk.PhotoImage(img2)
            lbl2 = tk.Label(f2, image=img2_tk)
            lbl2.image = img2_tk
            lbl2.pack(pady=(0, 8))
        except Exception:
            pass
    tk.Button(
        f2,
        text="📥 Tải SafeNet Client",
        command=lambda: webbrowser.open(SAFENET_URL),
        bg="#27ae60",
        fg="white",
        font=("Arial", 10, "bold"),
        width=18,
    ).pack()

    tk.Label(
        win,
        text="Sau khi cài driver -> cắm USB Token -> nhấn '🔌 Scan Token'.",
        fg="gray",
        justify="center",
    ).pack(pady=(14, 4))

    tk.Frame(win, height=1, bg="#dddddd").pack(fill="x", padx=20, pady=(8, 4))
    tk.Label(
        win,
        text="© Trần Mạnh Hùng | Phòng VH-XH xã Cư Jút, Lâm Đồng\n"
        "📞 0944624748   📧 hung@dno.vn",
        font=("Arial", 9),
        fg="#666666",
        justify="center",
    ).pack(pady=(0, 6))

    tk.Button(win, text="✅ Đóng", command=win.destroy, width=14).pack(pady=8)


def show_batch_result(parent, results: list):
    win = tk.Toplevel(parent)
    win.title("Kết quả ký hàng loạt")
    win.grab_set()
    _set_icon(win)

    pw, ph = 700, 460
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{pw}x{ph}+{(sw - pw) // 2}+{(sh - ph) // 2}")

    ok_count = sum(1 for r in results if r["ok"])
    err_count = len(results) - ok_count

    tk.Label(win, text=f"✅ Thành công: {ok_count}   ❌ Lỗi: {err_count}", font=("Arial", 13, "bold")).pack(
        pady=(14, 6)
    )

    cols = ("File", "Trạng thái", "Chi tiết")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=14)
    tree.heading("File", text="File")
    tree.heading("Trạng thái", text="Trạng thái")
    tree.heading("Chi tiết", text="Chi tiết / Output")
    tree.column("File", width=200, anchor="w")
    tree.column("Trạng thái", width=90, anchor="center")
    tree.column("Chi tiết", width=360, anchor="w")

    for r in results:
        status = "✅ OK" if r["ok"] else "❌ Lỗi"
        detail = r.get("out", "") if r["ok"] else r.get("err", "")
        tree.insert("", "end", values=(r["name"], status, detail))

    sb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=6)
    sb.pack(side="left", fill="y", pady=6)

    tk.Button(win, text="✅ Đóng", command=win.destroy, width=14).pack(side="bottom", pady=10)


# =====================
# PKCS11 HELPERS
# =====================
def _dedup_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _is_elf_shared_object(path: str) -> bool:
    try:
        if not os.path.isfile(path):
            return False
        with open(path, "rb") as f:
            head = f.read(4)
        return head == b"\x7fELF"
    except Exception:
        return False


def _collect_candidates_by_glob(patterns: List[str], search_dirs: List[str]) -> List[str]:
    found: List[str] = []
    for d in search_dirs:
        if not d or not os.path.isdir(d):
            continue
        for pat in patterns:
            found.extend(glob.glob(os.path.join(d, pat)))
    found = [p for p in found if _is_elf_shared_object(p)]
    return _dedup_keep_order(found)


def _normalize_cert_info(cert: dict, lib_path: str) -> dict:
    cert = dict(cert or {})
    cert.setdefault("module", lib_path)
    cert.setdefault("pkcs11_lib", lib_path)
    cert.setdefault("label", cert.get("label", ""))
    cert.setdefault("id", cert.get("id", cert.get("cka_id", "")))
    cert.setdefault("slot", cert.get("slot", ""))
    cert.setdefault("serial", cert.get("serial", cert.get("token_serial", "")))
    return cert


def _try_load_certs_from_lib(lib_path: str) -> Tuple[bool, List[dict], str]:
    try:
        certs = parse_certs(lib_path, CA_KEYWORDS)
        certs = certs or []
        certs = [_normalize_cert_info(c, lib_path) for c in certs]
        return True, certs, "OK"
    except Exception as e:
        return False, [], str(e)


def auto_find_working_pkcs11(saved_lib: str = "") -> Tuple[Optional[str], List[dict], str]:
    """
    Thử lần lượt:
    1. saved_lib nếu có
    2. PRIORITY_PKCS11
    3. FALLBACK_PKCS11
    4. scan glob toàn bộ các lib pkcs11 phổ biến
    Lib nào load được và nhìn thấy cert/token thì dùng luôn.
    """
    tried = set()

    def try_one(lib_path: str) -> Tuple[Optional[str], List[dict], str]:
        if not lib_path or lib_path in tried:
            return None, [], "skip"
        tried.add(lib_path)

        if not _is_elf_shared_object(lib_path):
            return None, [], "not_elf"

        ok, certs, msg = _try_load_certs_from_lib(lib_path)
        if ok and certs:
            return lib_path, certs, "certs_ok"

        if ok:
            return None, [], "loaded_but_no_cert"

        return None, [], msg

    if saved_lib:
        lib, certs, reason = try_one(saved_lib)
        if lib:
            return lib, certs, "saved_lib_ok"

    for lib_path in PRIORITY_PKCS11:
        lib, certs, reason = try_one(lib_path)
        if lib:
            return lib, certs, "priority_ok"

    for lib_path in FALLBACK_PKCS11:
        lib, certs, reason = try_one(lib_path)
        if lib:
            return lib, certs, "fallback_ok"

    discovered = _collect_candidates_by_glob(GLOB_PATTERNS, SEARCH_DIRS)
    for lib_path in discovered:
        lib, certs, reason = try_one(lib_path)
        if lib:
            return lib, certs, "glob_ok"

    return None, [], "not_found"


# =====================
# GUI
# =====================
class SignGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(1000, 700)

        try:
            if os.path.exists(ICON_ICO):
                self.iconbitmap(ICON_ICO)
            if os.path.exists(ICON_PNG):
                self.iconphoto(True, tk.PhotoImage(file=ICON_PNG))
        except Exception:
            pass

        self.config_data = load_config(CONFIG_FILE)

        self.input_path: Optional[str] = None
        self.input_dir: Optional[str] = self.config_data.get("last_input_dir")
        self.work_dir = tempfile.mkdtemp(prefix="vgca_sign_")
        self.pdf_path: Optional[str] = None
        self.sig_png_path: Optional[str] = None

        self.doc: Optional[fitz.Document] = None
        self.page_count: int = 0
        self.current_page_index: int = 0

        self.canvas_img_tk = None
        self.current_page_pix = None
        self._canvas_offset = (0, 0)
        self._sig_preview_tk = None
        self._drag_mode: Optional[str] = None
        self._drag_start = None

        self.pkcs11_lib_var = tk.StringVar()
        self._cert_list: list = []
        self._selected_cert: Optional[dict] = None
        self._batch_files: list = []

        self.doc_no_var = tk.StringVar(value=self.config_data.get("last_doc_no", ""))
        self.day_var = tk.StringVar(value=self.config_data.get("last_day", ""))
        self.month_var = tk.StringVar(value=self.config_data.get("last_month", ""))
        self.year_var = tk.StringVar(value=self.config_data.get("last_year", ""))

        self.active_box_var = tk.StringVar(value="signature")

        self.signature_placement: Optional[SignPlacement] = self._dict_to_placement(self.config_data.get("sig_placement"))
        self.doc_no_placement: Optional[SignPlacement] = self._dict_to_placement(self.config_data.get("doc_no_placement"))
        self.day_placement: Optional[SignPlacement] = self._dict_to_placement(self.config_data.get("day_placement"))
        self.month_placement: Optional[SignPlacement] = self._dict_to_placement(self.config_data.get("month_placement"))
        self.year_placement: Optional[SignPlacement] = self._dict_to_placement(self.config_data.get("year_placement"))

        saved_page = self.config_data.get("last_page_index")
        if isinstance(saved_page, int) and saved_page >= 0:
            self.current_page_index = saved_page

        self._build_ui()
        self.center_window()

        saved_png = self.config_data.get("last_png", "")
        if saved_png and os.path.exists(saved_png):
            self._apply_png(saved_png)
        else:
            self.after(300, self._prompt_first_png)

        self.after(200, self.scan_token)
        self.after(500, self.check_browser_request)

    def check_browser_request(self):
        path = "/tmp/vgca_request.json"

        if not os.path.exists(path):
            return

        try:
            import json

            with open(path, "r", encoding="utf-8") as f:
                req = json.load(f)

            os.remove(path)
            print(req)

            # TODO: nếu sau này cần browser/native-host thì xử lý ở đây

        except Exception as e:
            print(e)

    @property
    def placement(self) -> Optional[SignPlacement]:
        return self.signature_placement

    @placement.setter
    def placement(self, val):
        self.signature_placement = val

    def center_window(self):
        self.update_idletasks()
        w, h = 1300, 800
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _prompt_first_png(self):
        messagebox.showinfo("Chọn mẫu chữ ký", "Lần đầu sử dụng!\nVui lòng chọn file PNG mẫu chữ ký.")
        self.choose_png()

    # =====================
    # CONFIG HELPERS
    # =====================
    def _save_config(self):
        try:
            save_config(CONFIG_FILE, self.config_data)
        except Exception:
            pass

    def _placement_to_dict(self, p: Optional[SignPlacement]) -> Optional[dict]:
        if not p:
            return None
        return {
            "page_index": int(p.page_index),
            "x": float(p.x),
            "y": float(p.y),
            "w": float(p.w),
            "h": float(p.h),
        }

    def _dict_to_placement(self, d) -> Optional[SignPlacement]:
        if not isinstance(d, dict):
            return None
        try:
            return SignPlacement(
                page_index=int(d.get("page_index", 0)),
                x=float(d.get("x", 0)),
                y=float(d.get("y", 0)),
                w=float(d.get("w", 120)),
                h=float(d.get("h", 30)),
            )
        except Exception:
            return None

    def _save_overlay_config(self):
        self.config_data["sig_placement"] = self._placement_to_dict(self.signature_placement)
        self.config_data["doc_no_placement"] = self._placement_to_dict(self.doc_no_placement)
        self.config_data["day_placement"] = self._placement_to_dict(self.day_placement)
        self.config_data["month_placement"] = self._placement_to_dict(self.month_placement)
        self.config_data["year_placement"] = self._placement_to_dict(self.year_placement)

        self.config_data["last_doc_no"] = self.doc_no_var.get().strip()
        self.config_data["last_day"] = self.day_var.get().strip()
        self.config_data["last_month"] = self.month_var.get().strip()
        self.config_data["last_year"] = self.year_var.get().strip()

        self.config_data["last_page_index"] = self.current_page_index
        self._save_config()

    def _get_active_name(self) -> str:
        return self.active_box_var.get()

    def _get_active_placement(self) -> Optional[SignPlacement]:
        return getattr(self, f"{self._get_active_name()}_placement", None)

    def _set_active_placement(self, p: Optional[SignPlacement]):
        setattr(self, f"{self._get_active_name()}_placement", p)

    def _default_size(self):
        return BOX_DEFAULT_SIZE.get(self._get_active_name(), (120.0, 32.0))

    # =====================
    # BUILD UI
    # =====================
    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=12, pady=6)
        tk.Label(top, text="🔐 VGCA Token Signing Tool", font=("Arial", 15, "bold")).pack(side="left")
        tk.Button(top, text="❌ Thoát", command=self._on_quit).pack(side="right")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=6, pady=2)

        tab_single = tk.Frame(self.nb)
        tab_batch = tk.Frame(self.nb)
        self.nb.add(tab_single, text="  📄 Ký 1 file  ")
        self.nb.add(tab_batch, text="  📦 Ký hàng loạt  ")

        self._build_single_tab(tab_single)
        self._build_batch_tab(tab_batch)

        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=12, pady=(0, 4))
        self.status_var = tk.StringVar(value="Sẵn sàng.")
        tk.Label(bottom, textvariable=self.status_var, fg="green", anchor="w", font=("Arial", 9)).pack(side="left")
        tk.Label(
            bottom,
            text="© Trần Mạnh Hùng | VH-XH xã Cư Jút, Lâm Đồng | 📞 0944624748 | hung@dno.vn",
            fg="#888888",
            anchor="e",
            font=("Arial", 9),
        ).pack(side="right")

    # =====================
    # TAB 1
    # =====================
    def _build_single_tab(self, parent):
        main = tk.Frame(parent)
        main.pack(fill="both", expand=True)

        left_outer = tk.Frame(main, width=LEFT_PANEL_WIDTH)
        left_outer.pack(side="left", fill="y")
        left_outer.pack_propagate(False)

        left_canvas = tk.Canvas(left_outer, width=LEFT_PANEL_WIDTH - 18, highlightthickness=0)
        left_sb = ttk.Scrollbar(left_outer, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_sb.set)
        left_sb.pack(side="right", fill="y")
        left_canvas.pack(side="left", fill="both", expand=True)

        left = tk.Frame(left_canvas)
        left_canvas.create_window((0, 0), window=left, anchor="nw")

        def _on_left_configure(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        left.bind("<Configure>", _on_left_configure)

        

        right = tk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        pad = {"padx": 8, "pady": 3}
        wrap = LEFT_PANEL_WIDTH - 40

        frm_in = tk.LabelFrame(left, text="📄 Tài liệu", padx=8, pady=6)
        frm_in.pack(fill="x", **pad)
        self.lbl_input = tk.Label(frm_in, text="Chưa chọn file", fg="gray", wraplength=wrap, justify="left")
        self.lbl_input.pack(anchor="w")
        tk.Button(frm_in, text="📂 Chọn file (doc/docx/xls/xlsx/pdf)", command=self.choose_input).pack(
            fill="x", pady=3
        )
        self.lbl_pdf = tk.Label(frm_in, text="PDF: (chưa có)", fg="gray", wraplength=wrap, justify="left")
        self.lbl_pdf.pack(anchor="w")

        frm_png = tk.LabelFrame(left, text="🖊️ Mẫu chữ ký (PNG)", padx=8, pady=6)
        frm_png.pack(fill="x", **pad)
        self.lbl_png = tk.Label(frm_png, text="Chưa chọn PNG", fg="gray", wraplength=wrap, justify="left")
        self.lbl_png.pack(anchor="w")
        tk.Button(frm_png, text="🖼️ Đổi PNG chữ ký", command=self.choose_png).pack(fill="x", pady=3)

        frm_meta = tk.LabelFrame(left, text="🧾 Thông tin văn bản", padx=8, pady=8)
        frm_meta.pack(fill="x", **pad)

        tk.Label(frm_meta, text="Số văn bản:", font=("Arial", 9, "bold")).pack(anchor="w")
        ent_no = tk.Entry(frm_meta, textvariable=self.doc_no_var, font=("Arial", 10))
        ent_no.pack(fill="x", pady=(0, 6))

        row_date = tk.Frame(frm_meta)
        row_date.pack(fill="x")

        col_d = tk.Frame(row_date)
        col_d.pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Label(col_d, text="Ngày", font=("Arial", 9, "bold")).pack(anchor="w")
        ent_day = tk.Entry(col_d, textvariable=self.day_var, font=("Arial", 10))
        ent_day.pack(fill="x")

        col_m = tk.Frame(row_date)
        col_m.pack(side="left", fill="x", expand=True, padx=4)
        tk.Label(col_m, text="Tháng", font=("Arial", 9, "bold")).pack(anchor="w")
        ent_month = tk.Entry(col_m, textvariable=self.month_var, font=("Arial", 10))
        ent_month.pack(fill="x")

        col_y = tk.Frame(row_date)
        col_y.pack(side="left", fill="x", expand=True, padx=(4, 0))
        tk.Label(col_y, text="Năm", font=("Arial", 9, "bold")).pack(anchor="w")
        ent_year = tk.Entry(col_y, textvariable=self.year_var, font=("Arial", 10))
        ent_year.pack(fill="x")

        def _on_meta_change(event=None):
            self._save_overlay_config()
            self._refresh_preview()

        for ent in (ent_no, ent_day, ent_month, ent_year):
            ent.bind("<KeyRelease>", _on_meta_change)

        frm_mode = tk.LabelFrame(left, text="🎯 Chọn vùng đang đặt vị trí (click lên PDF)", padx=8, pady=6)
        frm_mode.pack(fill="x", **pad)

        mode_row = tk.Frame(frm_mode)
        mode_row.pack(fill="x")
        modes = [
            ("✍️ Chữ ký", "signature"),
            ("📋 Số VB", "doc_no"),
            ("📅 Ngày", "day"),
            ("📅 Tháng", "month"),
            ("📅 Năm", "year"),
        ]
        for text, value in modes:
            color = BOX_COLORS[value]
            tk.Radiobutton(
                mode_row,
                text=text,
                value=value,
                variable=self.active_box_var,
                fg=color,
                font=("Arial", 9, "bold"),
                command=self._refresh_preview,
            ).pack(side="left", padx=3)

        tk.Button(
            frm_mode,
            text="🗑️ Xóa tất cả vị trí",
            command=self.clear_all_positions,
            fg="#c0392b",
            font=("Arial", 8),
        ).pack(anchor="e", pady=(4, 0))

        frm_page = tk.LabelFrame(left, text="📑 Trang", padx=8, pady=6)
        frm_page.pack(fill="x", **pad)
        rowp = tk.Frame(frm_page)
        rowp.pack(fill="x")
        tk.Label(rowp, text="Trang:").pack(side="left")
        self.page_sel = tk.Entry(rowp, width=8)
        self.page_sel.pack(side="left", padx=4)
        self.page_sel.insert(0, "1")
        tk.Button(rowp, text="Đi", command=self.go_to_page_from_entry).pack(side="left", padx=4)

        rowpn = tk.Frame(frm_page)
        rowpn.pack(fill="x", pady=4)
        tk.Button(rowpn, text="⬅ Prev", command=self.prev_page).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(rowpn, text="Next ➡", command=self.next_page).pack(side="left", expand=True, fill="x", padx=2)

        self.lbl_place = tk.Label(
            frm_page,
            text="Chọn vùng bên trên -> Click lên PDF để đặt vị trí.",
            fg="gray",
            wraplength=wrap,
            justify="left",
        )
        self.lbl_place.pack(anchor="w", pady=2)

        self._build_token_panel(left, wrap)

        frm_act = tk.LabelFrame(left, text="✅ Ký và xuất PDF", padx=8, pady=8)
        frm_act.pack(fill="x", **pad)
        tk.Button(
            frm_act,
            text="✅  KÝ PDF NGAY",
            command=self.sign_and_export,
            bg="#d62828",
            fg="white",
            font=("Arial", 14, "bold"),
            height=2,
        ).pack(fill="x", pady=4)

        frm_prev = tk.LabelFrame(
            right,
            text="👁️ Preview  |  Chọn vùng -> Click=đặt  |  Kéo=di chuyển  |  Góc vàng=resize",
            padx=4,
            pady=4,
        )
        frm_prev.pack(fill="both", expand=True, padx=(0, 6), pady=6)

        self.canvas = tk.Canvas(frm_prev, bg="white", cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Configure>", lambda e: self._refresh_preview())
        self._refresh_preview()

    # =====================
    # TAB 2
    # =====================
    def _build_batch_tab(self, parent):
        main = tk.Frame(parent)
        main.pack(fill="both", expand=True)

        left_outer = tk.Frame(main, width=LEFT_PANEL_WIDTH)
        left_outer.pack(side="left", fill="y")
        left_outer.pack_propagate(False)

        left_canvas = tk.Canvas(left_outer, width=LEFT_PANEL_WIDTH - 18, highlightthickness=0)
        left_sb = ttk.Scrollbar(left_outer, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_sb.set)
        left_sb.pack(side="right", fill="y")
        left_canvas.pack(side="left", fill="both", expand=True)

        left = tk.Frame(left_canvas)
        left_canvas.create_window((0, 0), window=left, anchor="nw")

        def _on_cfg(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        left.bind("<Configure>", _on_cfg)

        right = tk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        pad = {"padx": 8, "pady": 3}
        wrap = LEFT_PANEL_WIDTH - 40

        frm_info = tk.LabelFrame(left, text="ℹ️ Cấu hình ký (dùng chung với tab Ký 1 file)", padx=8, pady=6)
        frm_info.pack(fill="x", **pad)
        tk.Label(
            frm_info,
            text="PNG chữ ký và vị trí ký được lấy từ tab 'Ký 1 file'.\nHãy đặt vị trí ký ở tab đó trước khi ký hàng loạt.",
            fg="#555",
            wraplength=wrap,
            justify="left",
        ).pack(anchor="w")

        frm_meta_b = tk.LabelFrame(left, text="🧾 Thông tin văn bản (dùng chung)", padx=8, pady=8)
        frm_meta_b.pack(fill="x", **pad)

        tk.Label(frm_meta_b, text="Số văn bản:", font=("Arial", 9, "bold")).pack(anchor="w")
        ent_no_b = tk.Entry(frm_meta_b, textvariable=self.doc_no_var, font=("Arial", 10))
        ent_no_b.pack(fill="x", pady=(0, 6))

        row_date_b = tk.Frame(frm_meta_b)
        row_date_b.pack(fill="x")
        for label, var in [("Ngày", self.day_var), ("Tháng", self.month_var), ("Năm", self.year_var)]:
            col = tk.Frame(row_date_b)
            col.pack(side="left", fill="x", expand=True, padx=2)
            tk.Label(col, text=label, font=("Arial", 9, "bold")).pack(anchor="w")
            ent = tk.Entry(col, textvariable=var, font=("Arial", 10))
            ent.pack(fill="x")
            ent.bind("<KeyRelease>", lambda e: self._save_overlay_config())

        ent_no_b.bind("<KeyRelease>", lambda e: self._save_overlay_config())

        self._build_token_panel_batch(left, wrap)

        frm_files = tk.LabelFrame(right, text="📋 Danh sách file cần ký", padx=8, pady=6)
        frm_files.pack(fill="both", expand=True, pady=4, padx=6)

        btn_row = tk.Frame(frm_files)
        btn_row.pack(fill="x", pady=(0, 6))
        tk.Button(
            btn_row, text="➕ Thêm file", command=self.batch_add_files, bg="#27ae60", fg="white",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="➖ Xóa đã chọn", command=self.batch_remove_selected, bg="#e74c3c", fg="white").pack(
            side="left", padx=(0, 6)
        )
        tk.Button(btn_row, text="🗑️ Xóa tất cả", command=self.batch_clear_all, bg="#95a5a6", fg="white").pack(
            side="left"
        )

        cols = ("STT", "Tên file", "Thư mục")
        self.batch_tree = ttk.Treeview(frm_files, columns=cols, show="headings", height=14)
        self.batch_tree.heading("STT", text="#")
        self.batch_tree.heading("Tên file", text="Tên file")
        self.batch_tree.heading("Thư mục", text="Thư mục")
        self.batch_tree.column("STT", width=40, anchor="center")
        self.batch_tree.column("Tên file", width=260, anchor="w")
        self.batch_tree.column("Thư mục", width=340, anchor="w")

        sb = ttk.Scrollbar(frm_files, orient="vertical", command=self.batch_tree.yview)
        self.batch_tree.configure(yscrollcommand=sb.set)
        self.batch_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        frm_run = tk.LabelFrame(right, text="🚀 Thực hiện ký hàng loạt", padx=8, pady=8)
        frm_run.pack(fill="x", pady=4, padx=6)

        self.batch_progress_var = tk.DoubleVar(value=0)
        self.batch_progress = ttk.Progressbar(frm_run, variable=self.batch_progress_var, maximum=100, length=400)
        self.batch_progress.pack(fill="x", pady=(0, 6))

        self.batch_status_var = tk.StringVar(value="Chưa bắt đầu")
        tk.Label(frm_run, textvariable=self.batch_status_var, fg="#2c3e50", font=("Arial", 9)).pack(
            anchor="w", pady=(0, 6)
        )

        tk.Button(
            frm_run,
            text="🚀  KÝ HÀNG LOẠT NGAY",
            command=self.batch_sign_start,
            bg="#6a1b9a",
            fg="white",
            font=("Arial", 13, "bold"),
            height=2,
        ).pack(fill="x", pady=4)

    # =====================
    # TOKEN PANELS
    # =====================
    def _build_token_panel(self, parent, wrap=460):
        frm = tk.LabelFrame(parent, text="🔌 USB Token & Certificate", padx=8, pady=6)
        frm.pack(fill="x", padx=8, pady=3)
        self._build_token_inner(frm, wrap)

    def _build_token_panel_batch(self, parent, wrap=460):
        frm = tk.LabelFrame(parent, text="🔌 USB Token & Certificate", padx=8, pady=6)
        frm.pack(fill="x", padx=8, pady=3)
        tk.Label(frm, text="Token & Certificate dùng chung với tab 'Ký 1 file'.", fg="gray", wraplength=wrap).pack(
            anchor="w", pady=(0, 4)
        )
        row = tk.Frame(frm)
        row.pack(fill="x")
        tk.Button(row, text="🔌 Scan Token", command=self.scan_token, bg="#2c3e50", fg="white").pack(
            side="left", expand=True, fill="x", padx=(0, 3)
        )
        tk.Button(row, text="🔄 Load Certs", command=self.load_certs_ui, bg="#1abc9c", fg="white").pack(
            side="left", expand=True, fill="x"
        )

    def _build_token_inner(self, frm, wrap=460):
        self.lbl_token = tk.Label(frm, text="🔍 Đang quét...", font=("Arial", 10, "bold"), fg="gray", wraplength=wrap)
        self.lbl_token.pack(anchor="w", pady=(0, 4))

        self.pkcs11_entry = tk.Entry(frm, textvariable=self.pkcs11_lib_var, state="readonly", fg="#555")
        self.pkcs11_entry.pack(fill="x", pady=2)

        row_scan = tk.Frame(frm)
        row_scan.pack(fill="x", pady=4)
        tk.Button(row_scan, text="🔌 Scan Token", command=self.scan_token, bg="#2c3e50", fg="white").pack(
            side="left", expand=True, fill="x", padx=(0, 3)
        )
        tk.Button(row_scan, text="📂 Chọn .so", command=self.choose_pkcs11).pack(side="left", expand=True, fill="x")

        tk.Label(frm, text="🔐 Certificate:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(6, 0))

        cert_row = tk.Frame(frm)
        cert_row.pack(fill="x", pady=2)
        self.cert_combo_var = tk.StringVar(value="(Chưa load)")
        self.cert_combo = ttk.Combobox(cert_row, textvariable=self.cert_combo_var, state="readonly", width=36)
        self.cert_combo.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.cert_combo.bind("<<ComboboxSelected>>", self._on_cert_selected)
        tk.Button(cert_row, text="ℹ️", command=self._show_selected_cert_detail, width=3).pack(side="left")

        tk.Button(
            frm,
            text="🔄 Load Certificates từ Token",
            command=self.load_certs_ui,
            bg="#1abc9c",
            fg="white",
            font=("Arial", 9, "bold"),
        ).pack(fill="x", pady=(4, 2))

        self.lbl_cert_info = tk.Label(frm, text="", fg="#2c3e50", wraplength=wrap, justify="left", font=("Arial", 8))
        self.lbl_cert_info.pack(anchor="w", pady=2)

        tk.Button(
            frm,
            text="📦 Chưa có driver? Xem hướng dẫn cài",
            command=lambda: show_driver_suggestion(self),
            fg="#2980b9"
        ).pack(fill="x", pady=(4, 0))

    # =====================
    # QUIT
    # =====================
    def _on_quit(self):
        try:
            if self.doc:
                self.doc.close()
        except Exception:
            pass
        try:
            shutil.rmtree(self.work_dir, ignore_errors=True)
        except Exception:
            pass
        self.destroy()

    # =====================
    # TOKEN SCAN / CERT
    # =====================
    def scan_token(self):
        self.lbl_token.config(text="🔍 Đang quét USB Token...", fg="gray")
        self.status_var.set("🔍 Đang thử PKCS#11: Bit4id -> SafeNet -> Fallback...")
        self.update_idletasks()

        saved_lib = self.config_data.get("pkcs11_lib", "").strip()
        lib, certs, reason = auto_find_working_pkcs11(saved_lib)

        if lib and os.path.exists(lib):
            self.pkcs11_lib_var.set(lib)
            self.config_data["pkcs11_lib"] = lib
            self._save_config()

            self._cert_list = certs

            if certs:
                values = [c.get("display", "(không tên)") for c in certs]
                self.cert_combo["values"] = values
                self.cert_combo_var.set(values[0])
                self._selected_cert = certs[0]
                self._update_cert_info(certs[0])
                self.lbl_token.config(text=f"🔌 Token OK: {os.path.basename(lib)} ✅", fg="#27ae60")
                self.status_var.set(f"✅ Đã nhận token qua {os.path.basename(lib)} | {len(certs)} cert")
            else:
                self.lbl_token.config(text=f"🔌 Đã nạp lib: {os.path.basename(lib)}", fg="#f39c12")
                self.status_var.set(f"⚠️ Lib load được nhưng chưa thấy certificate: {os.path.basename(lib)}")
        else:
            self.pkcs11_lib_var.set("")
            self._cert_list = []
            self._selected_cert = None
            self.cert_combo["values"] = []
            self.cert_combo_var.set("(Không tìm thấy cert)")
            self.lbl_cert_info.config(text="⚠️ Không tìm thấy certificate.")
            self.lbl_token.config(text="❌ Không tìm thấy driver PKCS#11 phù hợp", fg="#e74c3c")
            self.status_var.set("⚠️ Không tìm thấy token/driver phù hợp. Có thể chọn .so thủ công.")
            show_driver_suggestion(self)

    def load_certs_ui(self):
        lib = self.pkcs11_lib_var.get().strip()
        if not lib or not os.path.exists(lib):
            messagebox.showerror("Lỗi", "Chưa có PKCS#11 module.\nNhấn 'Scan Token' trước.")
            return

        self.status_var.set("🔄 Đang đọc certificates từ token...")
        self.update_idletasks()

        try:
            certs = parse_certs(lib, CA_KEYWORDS)
            certs = certs or []
            certs = [_normalize_cert_info(c, lib) for c in certs]
        except Exception as e:
            self.status_var.set("❌ Lỗi đọc certificate")
            messagebox.showerror("Lỗi load cert", str(e))
            return

        self._cert_list = certs

        if not certs:
            self.cert_combo["values"] = []
            self.cert_combo_var.set("(Không tìm thấy cert)")
            self.lbl_cert_info.config(text="⚠️ Không tìm thấy certificate.")
            self.status_var.set("⚠️ Không tìm thấy certificate")
            return

        values = [c.get("display", "(không tên)") for c in certs]
        self.cert_combo["values"] = values
        self.cert_combo_var.set(values[0])
        self._selected_cert = certs[0]
        self._update_cert_info(certs[0])
        self.status_var.set(f"✅ Tìm thấy {len(certs)} certificate")

    def _on_cert_selected(self, event=None):
        selected = self.cert_combo_var.get()
        for c in self._cert_list:
            if c.get("display", "") == selected:
                self._selected_cert = c
                self._update_cert_info(c)
                break

    def _update_cert_info(self, cert: dict):
        info = (
            f"👤 {cert.get('cn', '')}\n"
            f"🏢 {cert.get('org', '')}\n"
            f"🔑 ID: {cert.get('id', cert.get('cka_id', ''))} | Slot: {cert.get('slot', '')}"
        )
        self.lbl_cert_info.config(text=info)

    def _show_selected_cert_detail(self):
        if not self._selected_cert:
            messagebox.showinfo("Thông báo", "Chưa chọn certificate.")
            return
        show_cert_detail(self, self._selected_cert)

    def choose_pkcs11(self):
        path = filedialog.askopenfilename(
            title="Chọn PKCS#11 module (.so)",
            filetypes=[("Shared Object", "*.so"), ("All files", "*.*")]
        )
        if path:
            self.pkcs11_lib_var.set(path)
            self.config_data["pkcs11_lib"] = path
            self._save_config()
            self.lbl_token.config(text=f"🔌 Manual: {os.path.basename(path)} ✅", fg="#8e44ad")
            self.status_var.set(f"✅ PKCS#11: {os.path.basename(path)}")
            self.after(200, self.load_certs_ui)

    # =====================
    # PNG
    # =====================
    def _apply_png(self, path: str):
        self.sig_png_path = path
        self.lbl_png.config(text=os.path.basename(path), fg="black")

    def choose_png(self):
        path = filedialog.askopenfilename(
            title="Chọn PNG chữ ký",
            filetypes=[("PNG", "*.png"), ("All files", "*.*")]
        )
        if not path:
            return
        if os.path.splitext(path)[1].lower() not in SUPPORTED_PNG_EXT:
            messagebox.showerror("Lỗi", "Chỉ hỗ trợ PNG.")
            return
        self._apply_png(path)
        self.config_data["last_png"] = path
        self._save_config()
        self._refresh_preview()

    # =====================
    # INPUT FILE
    # =====================
    def choose_input(self):
        init_dir = self.config_data.get("last_input_dir", "")
        path = filedialog.askopenfilename(
            title="Chọn tài liệu cần ký",
            initialdir=init_dir if init_dir and os.path.isdir(init_dir) else "",
            filetypes=[("Documents", "*.doc *.docx *.xls *.xlsx *.pdf"), ("All files", "*.*")],
        )
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_INPUT_EXT:
            messagebox.showerror("Lỗi", f"Chỉ hỗ trợ: {', '.join(sorted(SUPPORTED_INPUT_EXT))}")
            return

        self.input_path = path
        self.input_dir = os.path.dirname(path)
        self.lbl_input.config(text=os.path.basename(path), fg="black")
        self.config_data["last_input_dir"] = self.input_dir
        self._save_config()

        self.status_var.set("Đang chuẩn bị PDF...")
        self.update_idletasks()

        try:
            self.pdf_path = path if ext == ".pdf" else convert_to_pdf(path, self.work_dir)
            self.lbl_pdf.config(text=os.path.basename(self.pdf_path), fg="black")
            self.load_pdf(self.pdf_path)
            self.status_var.set("✅ PDF sẵn sàng. Chọn vùng -> Click để đặt vị trí.")
        except Exception as e:
            self.status_var.set("❌ Lỗi chuẩn bị PDF.")
            messagebox.showerror("Lỗi convert/đọc PDF", str(e))

    def load_pdf(self, pdf_path: str):
        if self.doc:
            try:
                self.doc.close()
            except Exception:
                pass

        self.doc = fitz.open(pdf_path)
        self.page_count = self.doc.page_count

        saved_page = self.config_data.get("last_page_index")
        if isinstance(saved_page, int) and 0 <= saved_page < self.page_count:
            self.current_page_index = saved_page
        else:
            self.current_page_index = 0

        self.page_sel.delete(0, tk.END)
        self.page_sel.insert(0, str(self.current_page_index + 1))
        self._refresh_preview()

    # =====================
    # RENDER / PREVIEW
    # =====================
    def _render_page_to_tk(self, page_index: int):
        if self.doc is None:
            self.canvas.delete("all")
            self.canvas.configure(bg="white")
            return

        page = self.doc.load_page(page_index)
        cw = max(self.canvas.winfo_width(), 100)
        ch = max(self.canvas.winfo_height(), 100)
        rect = page.rect
        zoom = min(cw / rect.width, ch / rect.height)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        self.current_page_pix = pix

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.canvas_img_tk = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.configure(bg="white")

        ox = max((cw - pix.width) // 2, 0)
        oy = max((ch - pix.height) // 2, 0)
        self._canvas_offset = (ox, oy)
        self.canvas.create_image(ox, oy, anchor="nw", image=self.canvas_img_tk)

        self._draw_one_overlay(self.signature_placement, "signature", self.sig_png_path or "")
        self._draw_one_overlay(self.doc_no_placement, "doc_no", self.doc_no_var.get().strip())
        self._draw_one_overlay(self.day_placement, "day", self.day_var.get().strip())
        self._draw_one_overlay(self.month_placement, "month", self.month_var.get().strip())
        self._draw_one_overlay(self.year_placement, "year", self.year_var.get().strip())

        self.status_var.set(f"Trang {page_index + 1}/{self.page_count}")

    def _draw_one_overlay(self, placement: Optional[SignPlacement], box_name: str, text_or_path: str):
        if not placement or not self.current_page_pix:
            return
        if placement.page_index != self.current_page_index:
            return

        ox, oy = self._canvas_offset
        x1 = placement.x + ox
        y1 = placement.y + oy
        x2 = x1 + placement.w
        y2 = y1 + placement.h

        color = BOX_COLORS[box_name]
        is_active = (self._get_active_name() == box_name)

        if box_name == "signature":
            if text_or_path and os.path.exists(text_or_path):
                try:
                    pw = max(1, int(placement.w))
                    ph = max(1, int(placement.h))
                    img_src = Image.open(text_or_path).convert("RGBA")
                    img_src = img_src.resize((pw, ph), Image.LANCZOS)
                    bg = Image.new("RGBA", (pw, ph), (255, 255, 255, 0))
                    bg.paste(img_src, mask=img_src.split()[3])
                    self._sig_preview_tk = ImageTk.PhotoImage(bg.convert("RGB"))
                    self.canvas.create_image(x1, y1, anchor="nw", image=self._sig_preview_tk)
                except Exception:
                    pass
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="#fffff8", outline="")
            display = text_or_path if text_or_path else ""
            if display:
                font_size = max(9, int(placement.h * 0.55))
                self.canvas.create_text(
                    x1 + placement.w / 2,
                    y1 + placement.h / 2,
                    text=display,
                    fill="black",
                    font=("Arial", font_size, "bold"),
                    anchor="center",
                )

        lw = 3 if is_active else 1
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=lw, dash=(5, 3))

        if is_active:
            for (cx, cy) in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                self.canvas.create_rectangle(
                    cx - CORNER_HIT,
                    cy - CORNER_HIT,
                    cx + CORNER_HIT,
                    cy + CORNER_HIT,
                    fill="#FFD700",
                    outline="#FF8C00",
                    width=2,
                )

    def _refresh_preview(self):
        self.after(30, lambda: self._render_page_to_tk(self.current_page_index))

    # =====================
    # NAVIGATION
    # =====================
    def prev_page(self):
        if self.doc and self.current_page_index > 0:
            self.current_page_index -= 1
            self.page_sel.delete(0, tk.END)
            self.page_sel.insert(0, str(self.current_page_index + 1))
            self.config_data["last_page_index"] = self.current_page_index
            self._save_config()
            self._refresh_preview()

    def next_page(self):
        if self.doc and self.current_page_index < self.page_count - 1:
            self.current_page_index += 1
            self.page_sel.delete(0, tk.END)
            self.page_sel.insert(0, str(self.current_page_index + 1))
            self.config_data["last_page_index"] = self.current_page_index
            self._save_config()
            self._refresh_preview()

    def go_to_page_from_entry(self):
        if not self.doc:
            return
        try:
            idx = self._parse_page_selector(self.page_sel.get(), self.page_count)
            self.current_page_index = idx
            self.config_data["last_page_index"] = self.current_page_index
            self._save_config()
            self._refresh_preview()
        except Exception as e:
            messagebox.showerror("Lỗi trang", str(e))

    def _parse_page_selector(self, s: str, page_count: int) -> int:
        s = s.strip()
        m = re.match(r"^(\d+)(?:\s*/\s*(\d+))?$", s)
        if not m:
            raise ValueError("Trang phải có dạng: 1 hoặc 1/12")
        p = int(m.group(1))
        if p < 1 or p > page_count:
            raise ValueError(f"Trang phải trong khoảng 1..{page_count}")
        return p - 1

    # =====================
    # MOUSE EVENTS
    # =====================
    def _get_corner(self, mx: float, my: float) -> Optional[str]:
        p = self._get_active_placement()
        if not p:
            return None
        ox, oy = self._canvas_offset
        x1 = p.x + ox
        y1 = p.y + oy
        x2 = x1 + p.w
        y2 = y1 + p.h
        for name, (cx, cy) in [("tl", (x1, y1)), ("tr", (x2, y1)), ("bl", (x1, y2)), ("br", (x2, y2))]:
            if abs(mx - cx) <= CORNER_HIT and abs(my - cy) <= CORNER_HIT:
                return name
        return None

    def _inside_box(self, mx: float, my: float) -> bool:
        p = self._get_active_placement()
        if not p:
            return False
        ox, oy = self._canvas_offset
        x1 = p.x + ox
        y1 = p.y + oy
        x2 = x1 + p.w
        y2 = y1 + p.h
        return x1 < mx < x2 and y1 < my < y2

    def on_mouse_down(self, event):
        if not self.doc or not self.current_page_pix:
            return

        active_name = self._get_active_name()
        if active_name == "signature" and not self.sig_png_path:
            messagebox.showwarning("Thiếu chữ ký PNG", "Bạn cần chọn PNG chữ ký trước.")
            return

        mx, my = float(event.x), float(event.y)
        corner = self._get_corner(mx, my)
        active = self._get_active_placement()

        if corner:
            self._drag_mode = corner
            self._drag_start = (mx, my)
        elif self._inside_box(mx, my):
            self._drag_mode = "move"
            ox, oy = self._canvas_offset
            self._drag_start = (mx - active.x - ox, my - active.y - oy)
        else:
            ox, oy = self._canvas_offset
            rx = mx - ox
            ry = my - oy
            pw = self.current_page_pix.width
            ph = self.current_page_pix.height
            dw, dh = self._default_size()
            rx = max(0.0, min(rx, pw - dw))
            ry = max(0.0, min(ry, ph - dh))
            new_p = SignPlacement(page_index=self.current_page_index, x=rx, y=ry, w=dw, h=dh)
            self._set_active_placement(new_p)
            self._drag_mode = None
            self._save_overlay_config()
            self._update_place_label()
            self._refresh_preview()

    def on_mouse_drag(self, event):
        p = self._get_active_placement()
        if not p or not self._drag_mode:
            return

        mx, my = float(event.x), float(event.y)
        ox, oy = self._canvas_offset
        pw = self.current_page_pix.width if self.current_page_pix else 9999
        ph = self.current_page_pix.height if self.current_page_pix else 9999
        MIN_W, MIN_H = 35.0, 20.0

        if self._drag_mode == "move":
            dx, dy = self._drag_start
            p.x = max(0.0, min(mx - ox - dx, pw - p.w))
            p.y = max(0.0, min(my - oy - dy, ph - p.h))
        else:
            rx, ry = mx - ox, my - oy
            if self._drag_mode == "br":
                p.w = max(MIN_W, rx - p.x)
                p.h = max(MIN_H, ry - p.y)
            elif self._drag_mode == "tr":
                new_y = min(ry, p.y + p.h - MIN_H)
                p.h += p.y - new_y
                p.y = new_y
                p.w = max(MIN_W, rx - p.x)
            elif self._drag_mode == "bl":
                new_x = min(rx, p.x + p.w - MIN_W)
                p.w += p.x - new_x
                p.x = new_x
                p.h = max(MIN_H, ry - p.y)
            elif self._drag_mode == "tl":
                new_x = min(rx, p.x + p.w - MIN_W)
                new_y = min(ry, p.y + p.h - MIN_H)
                p.w += p.x - new_x
                p.h += p.y - new_y
                p.x = new_x
                p.y = new_y

        self._save_overlay_config()
        self._render_page_to_tk(self.current_page_index)

    def on_mouse_up(self, event):
        self._save_overlay_config()
        self._drag_mode = None
        self._drag_start = None

    def _update_place_label(self):
        p = self._get_active_placement()
        if not p:
            return
        name = BOX_LABELS.get(self._get_active_name(), "")
        self.lbl_place.config(
            text=f"✅ [{name}] Trang {p.page_index + 1}  |  x={int(p.x)} y={int(p.y)}  w={int(p.w)} h={int(p.h)}\n"
                 f"Kéo=di chuyển · Góc vàng=resize",
            fg="black",
        )

    def clear_all_positions(self):
        self.signature_placement = None
        self.doc_no_placement = None
        self.day_placement = None
        self.month_placement = None
        self.year_placement = None
        self._save_overlay_config()
        self.lbl_place.config(text="Đã xóa tất cả vị trí.", fg="gray")
        self._refresh_preview()

    # =====================
    # SIGN 1 FILE
    # =====================
    def sign_and_export(self):
        if not self.pdf_path or not self.doc:
            messagebox.showwarning("Thiếu tài liệu", "Bạn chưa chọn tài liệu.")
            return
        if not self.sig_png_path:
            messagebox.showwarning("Thiếu PNG", "Bạn chưa chọn PNG chữ ký.")
            return
        if not self.signature_placement:
            messagebox.showwarning(
                "Thiếu vị trí chữ ký",
                "Bạn chưa đặt vị trí chữ ký.\nChọn 'Chữ ký' rồi click lên PDF."
            )
            return
        if not self._selected_cert:
            messagebox.showwarning(
                "Thiếu Certificate",
                "Bạn chưa chọn certificate.\nNhấn 'Load Certificates từ Token' trước."
            )
            return

        pkcs11_lib = self.pkcs11_lib_var.get().strip()
        if not pkcs11_lib or not os.path.exists(pkcs11_lib):
            messagebox.showerror("Thiếu PKCS#11", "Chưa chọn PKCS#11 module.")
            return

        pin = simpledialog.askstring("Nhập PIN", "Nhập PIN USB Token:", show="*")
        if not pin:
            return

        cert = dict(self._selected_cert)
        cert.setdefault("pkcs11_lib", pkcs11_lib)
        cert.setdefault("module", pkcs11_lib)

        base_in = os.path.splitext(os.path.basename(self.input_path))[0] if self.input_path else "output"
        out_dir = self.input_dir or os.path.dirname(self.pdf_path)
        out_pdf = os.path.join(out_dir, base_in + "_signed.pdf")

        doc_no = self.doc_no_var.get().strip()
        day = self.day_var.get().strip()
        month = self.month_var.get().strip()
        year = self.year_var.get().strip()

        try:
            self.status_var.set(f"Đang ký: {base_in}...")
            self.update_idletasks()

            sign_one_pdf(
                pdf_path=self.pdf_path,
                out_path=out_pdf,
                placement=self.signature_placement,
                png_path=self.sig_png_path,
                page_pix_w=self.current_page_pix.width,
                page_pix_h=self.current_page_pix.height,
                pkcs11_lib=pkcs11_lib,
                pin=pin,
                cert=cert,
                work_dir=self.work_dir,
            )

            self.status_var.set(f"✅ Ký xong: {out_pdf}")

            info_extra = ""
            if doc_no:
                info_extra += f"\n📋 Số VB: {doc_no}"
            if day or month or year:
                info_extra += f"\n📅 Ngày: {day}/{month}/{year}"

            messagebox.showinfo(
                "Thành công",
                f"✅ Ký PDF thành công!\n\n👤 Người ký: {cert.get('cn', '')}{info_extra}\n📁 {out_pdf}",
            )

        except Exception as e:
            self.status_var.set("❌ Ký lỗi.")
            messagebox.showerror("Lỗi ký", str(e))

    # =====================
    # BATCH
    # =====================
    def batch_add_files(self):
        init_dir = self.config_data.get("last_input_dir", "")
        paths = filedialog.askopenfilenames(
            title="Chọn file cần ký (có thể chọn nhiều)",
            initialdir=init_dir if init_dir and os.path.isdir(init_dir) else "",
            filetypes=[("Documents", "*.doc *.docx *.xls *.xlsx *.pdf"), ("All files", "*.*")],
        )
        added = 0
        for p in paths:
            ext = os.path.splitext(p)[1].lower()
            if ext not in SUPPORTED_INPUT_EXT:
                continue
            if p not in self._batch_files:
                self._batch_files.append(p)
                added += 1
                self.config_data["last_input_dir"] = os.path.dirname(p)
                self._save_config()
        self._refresh_batch_tree()
        self.status_var.set(f"✅ Đã thêm {added} file. Tổng: {len(self._batch_files)} file.")

    def batch_remove_selected(self):
        selected = self.batch_tree.selection()
        if not selected:
            return
        indices = sorted([self.batch_tree.index(s) for s in selected], reverse=True)
        for i in indices:
            if 0 <= i < len(self._batch_files):
                self._batch_files.pop(i)
        self._refresh_batch_tree()

    def batch_clear_all(self):
        self._batch_files.clear()
        self._refresh_batch_tree()
        self.status_var.set("Đã xóa tất cả file.")

    def _refresh_batch_tree(self):
        for row in self.batch_tree.get_children():
            self.batch_tree.delete(row)
        for i, p in enumerate(self._batch_files, 1):
            self.batch_tree.insert("", "end", values=(i, os.path.basename(p), os.path.dirname(p)))

    def batch_sign_start(self):
        if not self._batch_files:
            messagebox.showwarning("Chưa có file", "Bạn chưa thêm file nào vào danh sách.")
            return
        if not self.sig_png_path:
            messagebox.showwarning("Thiếu PNG", "Bạn chưa chọn PNG chữ ký.\nVào tab 'Ký 1 file' để chọn.")
            return
        if not self.signature_placement:
            messagebox.showwarning(
                "Thiếu vị trí",
                "Bạn chưa đặt vị trí chữ ký.\nVào tab 'Ký 1 file', chọn 'Chữ ký' và click lên PDF.",
            )
            return
        if not self._selected_cert:
            messagebox.showwarning("Thiếu Certificate", "Bạn chưa chọn certificate.")
            return

        pkcs11_lib = self.pkcs11_lib_var.get().strip()
        if not pkcs11_lib or not os.path.exists(pkcs11_lib):
            messagebox.showerror("Thiếu PKCS#11", "Chưa chọn PKCS#11 module.")
            return

        pin = simpledialog.askstring("Nhập PIN", "Nhập PIN USB Token:", show="*")
        if not pin:
            return

        cert = dict(self._selected_cert)
        cert.setdefault("pkcs11_lib", pkcs11_lib)
        cert.setdefault("module", pkcs11_lib)

        t = threading.Thread(
            target=self._batch_sign_worker,
            args=(
                list(self._batch_files),
                pin,
                pkcs11_lib,
                cert,
                self.sig_png_path,
                self.signature_placement,
                self.current_page_pix.width if self.current_page_pix else 794,
                self.current_page_pix.height if self.current_page_pix else 1123,
            ),
            daemon=True,
        )
        t.start()

    def _batch_sign_worker(self, files, pin, pkcs11_lib, cert, png_path, placement, pix_w, pix_h):
        total = len(files)
        results = []

        self.after(0, lambda: self.batch_progress_var.set(0))
        self.after(0, lambda: self.batch_status_var.set(f"Đang ký 0/{total}..."))

        for i, fpath in enumerate(files, 1):
            fname = os.path.basename(fpath)
            ext = os.path.splitext(fpath)[1].lower()
            out_dir = os.path.dirname(fpath)
            base = os.path.splitext(fname)[0]
            out_pdf = os.path.join(out_dir, base + "_signed.pdf")

            self.after(0, lambda n=fname, idx=i: self.batch_status_var.set(f"Đang ký {idx}/{total}: {n}"))
            try:
                pdf_path = fpath if ext == ".pdf" else convert_to_pdf(fpath, self.work_dir)
                sign_one_pdf(
                    pdf_path=pdf_path,
                    out_path=out_pdf,
                    placement=placement,
                    png_path=png_path,
                    page_pix_w=pix_w,
                    page_pix_h=pix_h,
                    pkcs11_lib=pkcs11_lib,
                    pin=pin,
                    cert=cert,
                    work_dir=self.work_dir,
                )
                results.append({"name": fname, "ok": True, "out": out_pdf})
            except Exception as e:
                results.append({"name": fname, "ok": False, "err": str(e)})

            pct = i / total * 100
            self.after(0, lambda p=pct: self.batch_progress_var.set(p))

        ok = sum(1 for r in results if r["ok"])
        err = len(results) - ok
        self.after(0, lambda: self.batch_status_var.set(f"✅ Hoàn thành: {ok} thành công, {err} lỗi"))
        self.after(0, lambda: self.status_var.set(f"✅ Batch xong: {ok}/{total} file ký thành công"))
        self.after(0, lambda: show_batch_result(self, results))


if __name__ == "__main__":
    app = SignGUI()
    app.mainloop()
