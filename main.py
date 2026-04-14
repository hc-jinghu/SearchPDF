"""
main.py
SearchPDF — PyQt6 GUI
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QProgressBar, QTextEdit, QComboBox, QFrame, QLineEdit, QMessageBox,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent

from ocr_worker import OCRWorker

# ---------------------------------------------------------------------------
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}

LANGUAGES = {
    "English":              "en",
    "Chinese (Simplified)": "ch",
    "Chinese (Traditional)":"chinese_cht",
    "Japanese":             "japan",
    "Korean":               "korean",
    "French":               "fr",
    "German":               "german",
    "Spanish":              "es",
}

STATUS_PENDING    = "Pending"
STATUS_PROCESSING = "Processing"
STATUS_DONE       = "Done"
STATUS_ERROR      = "Error"

STATUS_COLORS = {
    STATUS_PENDING:    "#888888",
    STATUS_PROCESSING: "#0078d4",
    STATUS_DONE:       "#2e7d32",
    STATUS_ERROR:      "#c62828",
}

DROP_STYLE_IDLE = """
    DropZone {
        border: 2px dashed #aaaaaa;
        border-radius: 8px;
        background: #f8f9fa;
    }
    DropZone:hover {
        border-color: #0078d4;
        background: #e8f4fd;
    }
"""

DROP_STYLE_HOVER = """
    DropZone {
        border: 2px dashed #0078d4;
        border-radius: 8px;
        background: #dceefb;
    }
"""

# ---------------------------------------------------------------------------

class DropZone(QFrame):
    """Accepts drag-and-drop or click-to-browse for image files."""

    from PyQt6.QtCore import pyqtSignal
    files_chosen = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(110)
        self.setStyleSheet(DROP_STYLE_IDLE)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)

        for text, style in (
            ("Drop images here or click to browse",
             "font-size:14px; color:#444; border:none; background:transparent;"),
            ("JPG · PNG · TIFF · BMP · WebP",
             "font-size:11px; color:#999; border:none; background:transparent;"),
        ):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(style)
            layout.addWidget(lbl)

    # -- mouse click opens file dialog
    def mousePressEvent(self, _event):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "",
            "Images (*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.webp)",
        )
        if paths:
            self.files_chosen.emit(paths)

    # -- drag & drop
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(DROP_STYLE_HOVER)

    def dragLeaveEvent(self, _event):
        self.setStyleSheet(DROP_STYLE_IDLE)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(DROP_STYLE_IDLE)
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if Path(url.toLocalFile()).suffix.lower() in SUPPORTED_EXTS
        ]
        if paths:
            self.files_chosen.emit(paths)


# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SearchPDF")
        self.setMinimumSize(860, 640)
        self.worker: OCRWorker | None = None
        self.output_dir = str(Path.home() / "Desktop")
        self._build_ui()

    # -----------------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------------

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Title
        title = QLabel("SearchPDF")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#111;")
        layout.addWidget(title)

        sub = QLabel("Batch-convert images to searchable PDFs using PaddleOCR — SearchPDF")
        sub.setStyleSheet("font-size:12px; color:#666; margin-bottom:2px;")
        layout.addWidget(sub)

        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.files_chosen.connect(self._add_files)
        layout.addWidget(self.drop_zone)

        # File table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File", "Status", "Progress", "Time"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 64)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(220)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Output + language row
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        out_lbl = QLabel("Output folder:")
        out_lbl.setStyleSheet("font-weight:600;")
        self.out_edit = QLineEdit(self.output_dir)
        self.out_edit.setReadOnly(True)
        out_btn = QPushButton("Browse…")
        out_btn.setFixedWidth(78)
        out_btn.clicked.connect(self._choose_output)

        lang_lbl = QLabel("Language:")
        lang_lbl.setStyleSheet("font-weight:600;")
        self.lang_combo = QComboBox()
        for name in LANGUAGES:
            self.lang_combo.addItem(name)
        self.lang_combo.setFixedWidth(180)

        ctrl.addWidget(out_lbl)
        ctrl.addWidget(self.out_edit, 3)
        ctrl.addWidget(out_btn)
        ctrl.addSpacing(16)
        ctrl.addWidget(lang_lbl)
        ctrl.addWidget(self.lang_combo)
        layout.addLayout(ctrl)

        # Buttons row
        btn_row = QHBoxLayout()

        self.clear_btn = QPushButton("Clear List")
        self.clear_btn.setFixedWidth(90)
        self.clear_btn.clicked.connect(self._clear_files)

        self.open_btn = QPushButton("Open Output Folder")
        self.open_btn.clicked.connect(self._open_output_folder)

        btn_row.addWidget(self.clear_btn)
        btn_row.addWidget(self.open_btn)
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setFixedWidth(78)
        self.cancel_btn.setStyleSheet("color:#c62828;")
        self.cancel_btn.clicked.connect(self._cancel)

        self.process_btn = QPushButton("Process All")
        self.process_btn.setFixedWidth(110)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background:#0078d4; color:white; border:none;
                padding:7px 18px; border-radius:4px;
                font-weight:600; font-size:13px;
            }
            QPushButton:hover   { background:#006cbf; }
            QPushButton:disabled{ background:#c0c0c0; color:#888; }
        """)
        self.process_btn.clicked.connect(self._start_processing)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.process_btn)
        layout.addLayout(btn_row)

        # Log panel
        log_lbl = QLabel("Log")
        log_lbl.setStyleSheet("font-weight:600; color:#555;")
        layout.addWidget(log_lbl)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(110)
        self.log.setStyleSheet(
            "font-family:monospace; font-size:11px; "
            "background:#1e1e1e; color:#d4d4d4; border-radius:4px;"
        )
        layout.addWidget(self.log)

    # -----------------------------------------------------------------------
    # File management
    # -----------------------------------------------------------------------

    def _existing_paths(self) -> set[str]:
        paths = set()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                paths.add(item.data(Qt.ItemDataRole.UserRole))
        return paths

    def _add_files(self, paths: list[str]):
        existing = self._existing_paths()
        added = 0
        for path in paths:
            if path in existing:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(Path(path).name)
            name_item.setData(Qt.ItemDataRole.UserRole, path)
            name_item.setToolTip(path)
            self.table.setItem(row, 0, name_item)

            status_item = QTableWidgetItem(STATUS_PENDING)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor(STATUS_COLORS[STATUS_PENDING]))
            self.table.setItem(row, 1, status_item)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(True)
            self.table.setCellWidget(row, 2, bar)

            time_item = QTableWidgetItem("—")
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, time_item)

            existing.add(path)
            added += 1

        if added:
            self._log(f"Added {added} file(s). Queue total: {self.table.rowCount()}")

    def _clear_files(self):
        if self.worker and self.worker.isRunning():
            return
        self.table.setRowCount(0)
        self._log("Queue cleared.")

    def _choose_output(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self.output_dir
        )
        if folder:
            self.output_dir = folder
            self.out_edit.setText(folder)

    def _open_output_folder(self):
        import subprocess, platform
        path = self.output_dir
        if platform.system() == "Darwin":
            subprocess.run(["open", path])
        elif platform.system() == "Windows":
            subprocess.run(["explorer", path])
        else:
            subprocess.run(["xdg-open", path])

    # -----------------------------------------------------------------------
    # Processing
    # -----------------------------------------------------------------------

    def _start_processing(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Files", "Add images to the queue first.")
            return

        files = [
            self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            for row in range(self.table.rowCount())
        ]

        # Reset all rows to pending
        for row in range(self.table.rowCount()):
            self._set_row_status(row, STATUS_PENDING)
            self.table.cellWidget(row, 2).setValue(0)
            self.table.item(row, 3).setText("—")

        lang_code = LANGUAGES[self.lang_combo.currentText()]
        self.worker = OCRWorker(files, self.output_dir, lang_code)
        self.worker.progress.connect(self._on_progress)
        self.worker.file_done.connect(self._on_file_done)
        self.worker.file_error.connect(self._on_file_error)
        self.worker.all_done.connect(self._on_all_done)
        self.worker.start()

        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self._log(
            f"Started — {len(files)} file(s) | lang={lang_code} | out={self.output_dir}"
        )
        self._log("Note: first run downloads PaddleOCR models (~100 MB), please wait.")

    def _cancel(self):
        if self.worker:
            self.worker.cancel()
            self._log("Cancelling after current file...")

    # -----------------------------------------------------------------------
    # Worker signals
    # -----------------------------------------------------------------------

    def _row_for(self, filename: str) -> int:
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == filename:
                return row
        return -1

    def _set_row_status(self, row: int, status: str):
        item = self.table.item(row, 1)
        if item:
            item.setText(status)
            item.setForeground(QColor(STATUS_COLORS.get(status, "#888")))

    def _on_progress(self, filename: str, pct: int):
        row = self._row_for(filename)
        if row >= 0:
            self._set_row_status(row, STATUS_PROCESSING)
            self.table.cellWidget(row, 2).setValue(pct)

    def _on_file_done(self, filename: str, elapsed: float):
        row = self._row_for(filename)
        if row >= 0:
            self._set_row_status(row, STATUS_DONE)
            self.table.cellWidget(row, 2).setValue(100)
            self.table.item(row, 3).setText(f"{elapsed:.1f}s")
        self._log(f"Done  {filename}  ({elapsed:.1f}s)")

    def _on_file_error(self, filename: str, msg: str):
        row = self._row_for(filename)
        if row >= 0:
            self._set_row_status(row, STATUS_ERROR)
        self._log(f"ERROR {filename}: {msg}")

    def _on_all_done(self):
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        done  = sum(1 for r in range(self.table.rowCount())
                    if self.table.item(r, 1).text() == STATUS_DONE)
        total = self.table.rowCount()
        self._log(f"Finished — {done}/{total} file(s) converted successfully.")

    # -----------------------------------------------------------------------
    # Log helper
    # -----------------------------------------------------------------------

    def _log(self, msg: str):
        self.log.append(f"> {msg}")
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())


# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
