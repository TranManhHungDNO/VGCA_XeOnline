import glob
import os
import subprocess
from typing import Optional


def detect_token_type() -> str:
    """
    Chỉ dùng để gợi ý nhanh.
    Không nên coi là logic chính.
    """
    try:
        out = subprocess.check_output(
            ["lsusb"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).lower()

        if "bit4id" in out:
            return "bit4id"

        if any(k in out for k in ["safenet", "etoken", "gemalto", "thales", "idprime"]):
            return "safenet"

        if any(k in out for k in ["viettel", "vnpt", "opensc"]):
            return "opensc"

        return "unknown"
    except Exception:
        return "unknown"


def get_pkcs11_for_token(token_type: str, token_pkcs11_map: dict) -> Optional[str]:
    """
    Trả về lib đầu tiên tồn tại theo map.
    """
    for lib in token_pkcs11_map.get(token_type, []):
        if lib and os.path.exists(lib):
            return lib
    return None


def auto_detect_pkcs11(common_pkcs11_libs: list[str]) -> Optional[str]:
    """
    Tự dò lib PKCS#11 phổ biến.
    Ưu tiên danh sách truyền vào trước, sau đó quét glob.
    """
    for lib in common_pkcs11_libs:
        if lib and os.path.exists(lib):
            return lib

    search_dirs = [
        "/usr/lib",
        "/usr/lib64",
        "/usr/lib/x86_64-linux-gnu",
        "/usr/local/lib",
        "/lib",
        "/lib64",
        "/lib/x86_64-linux-gnu",
        "/opt",
    ]

    patterns = [
        "libbit4*.so",
        "libeTPkcs11*.so",
        "libeToken*.so",
        "libIDPrimePKCS11*.so",
        "opensc-pkcs11*.so",
        "*pkcs11*.so",
    ]

    seen = set()

    for d in search_dirs:
        if not os.path.isdir(d):
            continue

        for pat in patterns:
            for path in glob.glob(os.path.join(d, pat)):
                if path in seen:
                    continue
                seen.add(path)
                if os.path.exists(path):
                    return path

    try:
        result = subprocess.run(
            ["find", "/usr", "/lib", "/opt", "-name", "*.so"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )

        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or not os.path.exists(line):
                continue

            low = line.lower()
            if any(k in low for k in ["bit4", "pkcs11", "etoken", "idprime", "opensc"]):
                return line
    except Exception:
        pass

    return None
