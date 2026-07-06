import re
import subprocess


def decode_escaped_utf8(s: str) -> str:
    """
    Chuyển chuỗi dạng 'Tr\\xE1\\xBA\\xA7n' thành 'Trần' (UTF-8).
    """
    try:
        # Bước 1: chuyển \xNN → byte latin-1
        tmp = re.sub(
            r'\\x([0-9A-Fa-f]{2})',
            lambda m: bytes.fromhex(m.group(1)).decode('latin-1'),
            s
        )
        # Bước 2: decode lại UTF-8
        return tmp.encode('latin-1').decode('utf-8')
    except Exception:
        return s


def parse_slots(pkcs11_lib: str) -> list[tuple[int, str]]:
    slots: list[tuple[int, str]] = []

    try:
        out = subprocess.check_output(
            ["pkcs11-tool", "--module", pkcs11_lib, "-L"],
            text=True,
            stderr=subprocess.STDOUT,
        )

        current_slot = None
        token_label = ""

        for line in out.splitlines():
            # bắt slot
            m = re.match(r"^\s*Slot\s+(\d+)", line)
            if m:
                if current_slot is not None:
                    slots.append((current_slot, token_label or "Token"))
                current_slot = int(m.group(1))
                token_label = ""

            # bắt token label
            if "token label" in line.lower() and ":" in line:
                token_label = line.split(":", 1)[-1].strip()

        if current_slot is not None:
            slots.append((current_slot, token_label or "Token"))

    except Exception as e:
        print(f"[parse_slots] error: {e}")

    if not slots:
        slots = [(0, "Token")]

    return slots


def parse_certs(pkcs11_lib: str, ca_keywords: list[str]) -> list[dict]:
    """
    Đọc cert từ tất cả slot.
    - Không yêu cầu PrivateKey visible (Bit4id OK)
    - Fix decode UTF-8 cho CN/ORG
    - Lọc CA/Root
    """

    all_certs: list[dict] = []

    for slot_no, token_label in parse_slots(pkcs11_lib):
        try:
            out = subprocess.check_output(
                ["pkcs11-tool", "--module", pkcs11_lib, "--slot", str(slot_no), "-O"],
                text=True,
                stderr=subprocess.STDOUT,
            )

            blocks = re.split(
                r"(?=^(?:Certificate|Private Key|Public Key) Object)",
                out,
                flags=re.MULTILINE,
            )

            for b in blocks:
                if not b.startswith("Certificate Object"):
                    continue

                id_m = re.search(r"^\s*ID:\s*(.+)$", b, re.MULTILINE)
                label_m = re.search(r"^\s*label:\s*(.+)$", b, re.MULTILINE)
                subj_m = re.search(r"^\s*subject:\s*DN:\s*(.+)$", b, re.MULTILINE)

                if not id_m:
                    continue

                cid = id_m.group(1).strip()
                label = label_m.group(1).strip() if label_m else cid
                subject = subj_m.group(1).strip() if subj_m else ""

                # parse DN
                cn_m = re.search(r"CN=([^,/]+)", subject)
                org_m = re.search(r"(?:^|,)\s*O=([^,/]+)", subject)
                email_m = re.search(r"emailAddress=([^,/\s]+)", subject)

                cn = decode_escaped_utf8(cn_m.group(1).strip()) if cn_m else label
                org = decode_escaped_utf8(org_m.group(1).strip()) if org_m else ""
                email = email_m.group(1).strip() if email_m else ""

                # lọc CA/root
                if any(k in cn.lower() for k in ca_keywords):
                    continue

                display = f"{cn} | {token_label} | Slot {slot_no}"

                all_certs.append(
                    {
                        "slot": slot_no,
                        "token": token_label,
                        "label": label,
                        "id": cid,
                        "cn": cn,
                        "org": org,
                        "email": email,
                        "display": display,
                    }
                )

        except Exception as e:
            print(f"[parse_certs] slot={slot_no} error: {e}")

    return all_certs
