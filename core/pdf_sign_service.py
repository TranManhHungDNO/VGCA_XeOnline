import os

import fitz  # PyMuPDF
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.pkcs11 import PKCS11Signer, open_pkcs11_session

from core.models import SignPlacement


def stamp_png_on_pdf(
    pdf_path: str,
    out_path: str,
    placement: SignPlacement,
    png_path: str,
    page_pix_w: float,
    page_pix_h: float,
):
    doc = fitz.open(pdf_path)
    page = doc.load_page(placement.page_index)
    rect = page.rect

    zoom_x = page_pix_w / rect.width
    zoom_y = page_pix_h / rect.height
    zoom = (zoom_x + zoom_y) / 2.0

    x0 = placement.x / zoom
    y0 = placement.y / zoom
    x1 = x0 + placement.w / zoom
    y1 = y0 + placement.h / zoom

    page.insert_image(fitz.Rect(x0, y0, x1, y1), filename=png_path)
    doc.save(out_path)
    doc.close()


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
    """Stamp PNG + ký số 1 file PDF. Raise nếu lỗi."""
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    stamped = os.path.join(work_dir, base + "_stamped_tmp.pdf")

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
        slot_no=cert["slot"],
    )

    pkcs11_signer = PKCS11Signer(
        pkcs11_session=session,
        cert_label=cert["label"],
        key_label=cert["label"],
        key_id=bytes.fromhex(cert["id"]),
    )

    with open(stamped, "rb") as inf:
        writer = IncrementalPdfFileWriter(inf)

        meta = signers.PdfSignatureMetadata(
            field_name="Signature1",
            reason="Signed with VGCA Token",
            location="Linux Mint",
        )

        # Ẩn field, chỉ còn PNG
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
