import os

import fitz  # PyMuPDF
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.pkcs11 import PKCS11Signer, open_pkcs11_session

from core.models import SignPlacement
from core.pkcs11_reader import cert_id_to_bytes


def stamp_png_on_pdf(
    pdf_path: str,
    out_path: str,
    placement: SignPlacement,
    png_path: str,
    page_pix_w: float,
    page_pix_h: float,
):
    """
    Đóng dấu ảnh PNG lên PDF theo tọa độ preview.
    """
    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(placement.page_index)
        rect = page.rect

        zoom_x = page_pix_w / rect.width if rect.width else 1.0
        zoom_y = page_pix_h / rect.height if rect.height else 1.0
        zoom = (zoom_x + zoom_y) / 2.0
        if zoom <= 0:
            zoom = 1.0

        x0 = placement.x / zoom
        y0 = placement.y / zoom
        x1 = x0 + placement.w / zoom
        y1 = y0 + placement.h / zoom

        page.insert_image(fitz.Rect(x0, y0, x1, y1), filename=png_path)
        doc.save(out_path)
    finally:
        doc.close()


def _build_signer_kwargs(cert: dict) -> list[dict]:
    """
    Trả về nhiều chiến lược signer để tương thích:
    1. key_id only                      -> hợp SafeNet
    2. key_id + cert_label + key_label  -> hybrid
    3. label only                       -> hợp một số Bit4id / token cũ
    """
    key_id = cert_id_to_bytes(cert)
    label = (cert.get("label") or "").strip()

    strategies: list[dict] = []

    if key_id:
        strategies.append(
            {
                "key_id": key_id,
            }
        )

        if label:
            strategies.append(
                {
                    "key_id": key_id,
                    "cert_label": label,
                    "key_label": label,
                }
            )

    if label:
        strategies.append(
            {
                "cert_label": label,
                "key_label": label,
            }
        )

    if not strategies:
        raise ValueError("Certificate không có cả label lẫn id/cka_id để tạo PKCS11Signer.")

    return strategies


def _sign_pdf_with_strategy(
    stamped_pdf: str,
    out_path: str,
    placement: SignPlacement,
    pkcs11_session,
    signer_kwargs: dict,
):
    pkcs11_signer = PKCS11Signer(
        pkcs11_session=pkcs11_session,
        **signer_kwargs,
    )

    with open(stamped_pdf, "rb") as inf:
        writer = IncrementalPdfFileWriter(inf)

        meta = signers.PdfSignatureMetadata(
            field_name="Signature1",
            reason="Signed with VGCA Token",
            location="Linux Mint",
        )

        field_spec = SigFieldSpec(
            sig_field_name="Signature1",
            on_page=placement.page_index,
            box=(0, 0, 0, 0),
        )

        pdf_signer = signers.PdfSigner(
            signature_meta=meta,
            signer=pkcs11_signer,
            new_field_spec=field_spec,
        )

        result = pdf_signer.sign_pdf(writer)

        with open(out_path, "wb") as outf:
            outf.write(result.getbuffer())


def sign_one_pdf(
    pdf_path: str,
    out_path: str,
    placement: SignPlacement,
    png_path: str,
    page_pix_w: float,
    page_pix_h: float,
    pkcs11_lib: str,
    pin: str,
    cert: dict,
    work_dir: str,
):
    """
    Stamp PNG + ký số 1 file PDF.
    Raise exception nếu lỗi.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Không tìm thấy PDF: {pdf_path}")

    if not os.path.exists(png_path):
        raise FileNotFoundError(f"Không tìm thấy PNG: {png_path}")

    if not os.path.exists(pkcs11_lib):
        raise FileNotFoundError(f"Không tìm thấy PKCS#11 lib: {pkcs11_lib}")

    if "slot" not in cert:
        raise ValueError("Certificate thiếu thông tin 'slot'.")

    base = os.path.splitext(os.path.basename(pdf_path))[0]
    stamped = os.path.join(work_dir, base + "_stamped_tmp.pdf")

    if os.path.exists(stamped):
        try:
            os.remove(stamped)
        except Exception:
            pass

    stamp_png_on_pdf(
        pdf_path=pdf_path,
        out_path=stamped,
        placement=placement,
        png_path=png_path,
        page_pix_w=page_pix_w,
        page_pix_h=page_pix_h,
    )

    session = open_pkcs11_session(
        lib_location=pkcs11_lib,
        user_pin=pin,
        slot_no=int(cert["slot"]),
    )

    try:
        strategies = _build_signer_kwargs(cert)
        errors: list[str] = []

        for idx, signer_kwargs in enumerate(strategies, 1):
            try:
                _sign_pdf_with_strategy(
                    stamped_pdf=stamped,
                    out_path=out_path,
                    placement=placement,
                    pkcs11_session=session,
                    signer_kwargs=signer_kwargs,
                )
                return
            except Exception as e:
                errors.append(f"Strategy {idx} failed: {e}")

        raise RuntimeError(
            "Không thể ký với các chiến lược PKCS#11 hiện có.\n" + "\n".join(errors)
        )

    finally:
        try:
            session.close()
        except Exception:
            pass
