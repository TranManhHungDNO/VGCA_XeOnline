import os
import shutil
import subprocess


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode, p.stdout, p.stderr


def ensure_libreoffice_exists():
    if shutil.which("libreoffice") is None:
        raise RuntimeError("Không tìm thấy 'libreoffice'. Hãy cài: sudo apt install -y libreoffice")


def convert_to_pdf(input_path: str, out_dir: str) -> str:
    ensure_libreoffice_exists()
    cmd = [
        "libreoffice", "--headless", "--nologo", "--nolockcheck",
        "--nodefault", "--nofirststartwizard",
        "--convert-to", "pdf", "--outdir", out_dir, input_path
    ]
    code, out, err = run_cmd(cmd)
    if code != 0:
        raise RuntimeError(f"LibreOffice convert lỗi.\nSTDOUT:\n{out}\nSTDERR:\n{err}")

    base = os.path.splitext(os.path.basename(input_path))[0]
    pdf_path = os.path.join(out_dir, base + ".pdf")

    if not os.path.exists(pdf_path):
        pdfs = [
            os.path.join(out_dir, f)
            for f in os.listdir(out_dir)
            if f.lower().endswith(".pdf")
        ]
        if not pdfs:
            raise RuntimeError("Convert xong nhưng không thấy file PDF output.")
        pdfs.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        pdf_path = pdfs[0]

    return pdf_path
