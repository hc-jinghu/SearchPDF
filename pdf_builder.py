"""
pdf_builder.py
Converts a single image + PaddleOCR results into a searchable PDF.

Pipeline:
  1. Open image to get pixel dimensions.
  2. Create a new PDF page (same size as image in points 1pt = 1px here).
  3. Embed the original image at full quality (JPEG stays JPEG, PNG stays PNG).
  4. Overlay each OCR text string as invisible text (PDF render mode 3)
     positioned at the bounding box returned by PaddleOCR.

The result is visually identical to the original image but fully Ctrl+F searchable.
"""

from __future__ import annotations

import fitz  # PyMuPDF
from PIL import Image


MIN_CONFIDENCE = 0.30   # discard OCR results below this threshold
MIN_BOX_PX     = 2      # ignore degenerate bounding boxes


def build_searchable_pdf(image_path: str, ocr_lines: list, output_path: str) -> None:
    """
    Parameters
    ----------
    image_path : str
        Path to the source image (JPG, PNG, TIFF, BMP, WebP …).
    ocr_lines : list
        PaddleOCR result lines. Each element is:
            [ [[x1,y1],[x2,y1],[x2,y2],[x1,y2]], ('text', confidence) ]
    output_path : str
        Where to write the resulting PDF.
    """
    # --- 1. Image dimensions ---
    with Image.open(image_path) as img:
        img_w, img_h = img.size
        # WebP and some exotic formats need transcoding before PyMuPDF can embed them
        needs_transcode = img.format not in ("JPEG", "PNG", "BMP", "TIFF")
        if needs_transcode:
            from io import BytesIO
            buf = BytesIO()
            img.save(buf, format="PNG")
            img_data = buf.getvalue()
        else:
            img_data = None

    # --- 2. New PDF document, one page matching image pixel size ---
    doc  = fitz.open()
    page = doc.new_page(width=img_w, height=img_h)
    rect = fitz.Rect(0, 0, img_w, img_h)

    # --- 3. Embed image (lossless for PNG/TIFF, original encoding for JPEG) ---
    if img_data is not None:
        page.insert_image(rect, stream=img_data)
    else:
        page.insert_image(rect, filename=image_path)

    # --- 4. Invisible text overlay ---
    for item in ocr_lines:
        if not item or len(item) < 2:
            continue

        bbox_pts, text_info = item
        if not text_info or len(text_info) < 2:
            continue

        text, confidence = text_info

        if confidence < MIN_CONFIDENCE or not text.strip():
            continue

        # bbox_pts may be a list or numpy array; normalise to floats
        try:
            xs = [float(p[0]) for p in bbox_pts]
            ys = [float(p[1]) for p in bbox_pts]
        except (TypeError, IndexError):
            continue

        x1, y1 = min(xs), min(ys)
        x2, y2 = max(xs), max(ys)

        box_h = y2 - y1
        box_w = x2 - x1
        if box_h < MIN_BOX_PX or box_w < MIN_BOX_PX:
            continue

        # Font size scaled to bounding box height
        fontsize = max(4.0, box_h * 0.85)

        # insert_text baseline = bottom-left corner of bounding box
        point = fitz.Point(x1, y2)

        try:
            page.insert_text(
                point,
                text,
                fontsize=fontsize,
                render_mode=3,   # PDF render mode 3 = invisible (but searchable)
                overlay=True,
            )
        except Exception:
            # Never let a single bad token abort the whole page
            continue

    # --- 5. Save with compression ---
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
