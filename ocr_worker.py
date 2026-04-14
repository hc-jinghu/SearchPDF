"""
ocr_worker.py
Runs PaddleOCR + pdf_builder in a background QThread so the GUI stays responsive.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal


class OCRWorker(QThread):
    # filename, percent (0-100)
    progress  = pyqtSignal(str, int)
    # filename, elapsed_seconds
    file_done = pyqtSignal(str, float)
    # filename, error message
    file_error = pyqtSignal(str, str)
    # emitted once when all files are processed (or cancelled)
    all_done  = pyqtSignal()

    def __init__(self, files: list[str], output_dir: str, language: str = "en", combine: bool = False):
        super().__init__()
        self.files      = files
        self.output_dir = output_dir
        self.language   = language
        self.combine    = combine
        self._cancelled = False

    # ------------------------------------------------------------------
    def run(self):
        # Import here so errors surface as signals, not crashes
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            self.file_error.emit("setup", f"PaddleOCR not found — run install.py first. ({exc})")
            self.all_done.emit()
            return

        from pdf_builder import build_pdf_page, build_searchable_pdf, merge_pdfs

        # Initialise once; PaddleOCR downloads models on first use (~100 MB)
        # show_log was removed in PaddleOCR >=2.8; suppress via logging module instead
        try:
            import logging
            logging.getLogger("ppocr").setLevel(logging.ERROR)
            ocr = PaddleOCR(use_angle_cls=True, lang=self.language)
        except Exception as exc:
            self.file_error.emit("setup", f"Failed to initialise PaddleOCR: {exc}")
            self.all_done.emit()
            return

        combined_docs = []  # used only when self.combine is True

        for file_path in self.files:
            if self._cancelled:
                break

            filename = Path(file_path).name
            start    = time.time()

            try:
                self.progress.emit(filename, 10)

                raw = ocr.ocr(file_path)

                self.progress.emit(filename, 60)

                lines = self._normalise_result(raw)

                self.progress.emit(filename, 75)

                if self.combine:
                    combined_docs.append(build_pdf_page(file_path, lines))
                else:
                    output_path = os.path.join(
                        self.output_dir,
                        Path(file_path).stem + ".pdf",
                    )
                    build_searchable_pdf(file_path, lines, output_path)

                self.progress.emit(filename, 100)
                self.file_done.emit(filename, time.time() - start)

            except Exception as exc:
                self.file_error.emit(filename, str(exc))

        if self.combine and combined_docs and not self._cancelled:
            try:
                combined_path = os.path.join(self.output_dir, "SearchPDF_combined.pdf")
                merge_pdfs(combined_docs, combined_path)
            except Exception as exc:
                self.file_error.emit("combined", f"Failed to merge PDFs: {exc}")

        self.all_done.emit()

    # ------------------------------------------------------------------
    def cancel(self):
        self._cancelled = True

    # ------------------------------------------------------------------
    @staticmethod
    def _normalise_result(raw) -> list:
        """
        PaddleOCR changed its return format between versions.
        Normalise to a flat list of [bbox, (text, score)] items.
        """
        if raw is None:
            return []

        # New format (>=2.6):  [[line, line, ...]]   (list-of-pages)
        if (
            isinstance(raw, list)
            and len(raw) > 0
            and isinstance(raw[0], list)
            and len(raw[0]) > 0
            and isinstance(raw[0][0], list)
        ):
            return raw[0] if raw[0] is not None else []

        # Old format:  [line, line, ...]
        return raw if raw else []
