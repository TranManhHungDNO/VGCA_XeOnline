import os
import subprocess
from typing import Optional


def detect_token_type() -> str:
    try:
        out = subprocess.check_output(
            ["lsusb"], text=True, stderr=subprocess.DEVNULL
        ).lower()

        if "bit4id" in out:
            return "bit4id"
        if any(k in out for k in ["safenet", "etoken", "gemalto", "thales"]):
            return "safenet"
        if "viettel" in out or "vnpt" in out:
            return "opensc"
        return "unknown"
    except Exception:
        return "unknown"


def get_pkcs11_for_token(token_type: str, token_pkcs11_map: dict) -> Optional[str]:
    for lib in token_pkcs11_map.get(token_type, []):
        if os.path.exists(lib):
            return lib
    return None


def auto_detect_pkcs11(common_pkcs11_libs: list[str]) -> Optional[str]:
    for lib in common_pkcs11_libs:
        if os.path.exists(lib):
            return lib

    try:
        result = subprocess.run(
            ["find", "/usr", "/lib", "/opt", "-name", "*.so", "-path", "*pkcs11*"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and os.path.exists(line):
                return line
    except Exception:
        pass

    return None
