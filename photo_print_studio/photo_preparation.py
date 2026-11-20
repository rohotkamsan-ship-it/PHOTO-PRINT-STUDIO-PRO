"""Photo preparation step shown before print layout."""
from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QFileDialog, QComboBox, QColorDialog, QMessageBox, QProgressDialog,
)
from .background_tools import prepare_image


class PhotoPreparationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Photo Preparation · PHOTO PRINT STUDIO PRO")
        self.resize(980, 680)
        self.source_paths: list[str] = []
        self.prepared_paths: list[str] = []
        self.background_color = "#ffffff"
        root = QVBoxLayout(self)
        heading = QLabel("STEP 1  ·  PHOTO PREPARATION")
        heading.setStyleSheet("font-size:20px;font-weight:700;color:#18324d")
        root.addWidget(heading)
        root.addWidget(QLabel("Load photos, optionally remove the background, choose a new color, then continue to print layout."))
        body = QHBoxLayout()
        self.files = QListWidget()
        body.addWidget(self.files, 1)
        side = QVBoxLayout()
        self.preview = QLabel("No photo selected")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(420, 420)
        self.preview.setStyleSheet("background:#e8edf3;border:1px dashed #9aaabd;border-radius:10px")
        side.addWidget(self.preview, 1)
        self.background = QComboBox()
        self.background.addItems(["Transparent", "White", "Blue", "Light Blue", "Red", "Custom color"])
        self.background.currentTextChanged.connect(self._background_changed)
        side.addWidget(QLabel("Background after removal"))
        side.addWidget(self.background)
        self.custom_button = QPushButton("Choose custom color")
        self.custom_button.clicked.connect(self._choose_color)
        side.addWidget(self.custom_button)
        body.addLayout(side, 2)
        root.addLayout(body, 1)
        actions = QHBoxLayout()
        load = QPushButton("＋ Load Images")
        load.clicked.connect(self.load_images)
        remove = QPushButton("Remove Background (Free AI)")
        remove.clicked.connect(self.remove_backgrounds)
        skip = QPushButton("Skip Editing")
        skip.clicked.connect(self.skip_editing)
        next_button = QPushButton("Next · Print Layout  →")
        next_button.setObjectName("primary")
        next_button.clicked.connect(self.continue_to_print)
        actions.addWidget(load)
        actions.addWidget(remove)
        actions.addStretch()
        actions.addWidget(skip)
        actions.addWidget(next_button)
        root.addLayout(actions)
        self.files.currentRowChanged.connect(self._show_preview)
        self.setStyleSheet("""
            QDialog{background:#f3f6fa}
            QPushButton{padding:10px 14px;border:1px solid #c5d1df;border-radius:7px;background:white;font-weight:600}
            QPushButton#primary{background:#1769aa;color:white}
            QListWidget{background:white;border:1px solid #d3dce7;border-radius:8px;padding:6px}
        """)

    def load_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Load Photos", "", "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff)")
        if paths:
            self.source_paths = paths
            self.prepared_paths = list(paths)
            self.files.clear()
            self.files.addItems([Path(p).name for p in paths])
            self.files.setCurrentRow(0)

    def _show_preview(self, row: int):
        if row < 0 or row >= len(self.prepared_paths):
            self.preview.setText("No photo selected")
            self.preview.setPixmap(QPixmap())
            return
        pix = QPixmap(self.prepared_paths[row])
        self.preview.setPixmap(pix.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._show_preview(self.files.currentRow())

    def _background_changed(self, value: str):
        self.custom_button.setEnabled(value == "Custom color")

    def _choose_color(self):
        color = QColorDialog.getColor(QColor(self.background_color), self, "Choose background color")
        if color.isValid():
            self.background_color = color.name()
            self.custom_button.setText(f"Custom color: {self.background_color}")

    def remove_backgrounds(self):
        if not self.source_paths:
            QMessageBox.information(self, "Load photos", "Please load at least one photo first.")
            return
        choice = self.background.currentText()
        colors = {"White": "#ffffff", "Blue": "#1677d2", "Light Blue": "#9fd5f5", "Red": "#d92736", "Custom color": self.background_color, "Transparent": None}
        color = colors.get(choice)
        progress = QProgressDialog("Removing photo backgrounds with the free AI model…", "Cancel", 0, len(self.source_paths), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        output_dir = Path.home() / "Pictures" / "PHOTO_PRINT_STUDIO_PRO" / "Prepared"
        results = []
        try:
            for index, source in enumerate(self.source_paths):
                if progress.wasCanceled():
                    break
                target = output_dir / f"{Path(source).stem}_prepared.png"
                progress.setValue(index)
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()
                results.append(prepare_image(source, str(target), color))
            progress.setValue(len(self.source_paths))
        except Exception as exc:
            QMessageBox.critical(self, "Background removal failed", str(exc))
            return
        if results:
            self.prepared_paths = results
            self.files.setCurrentRow(0)
            QMessageBox.information(self, "Finished", f"Prepared {len(results)} photo(s). Files saved in:\\n{output_dir}")

    def skip_editing(self):
        if not self.source_paths:
            QMessageBox.information(self, "Load photos", "Please load photos first.")
            return
        self.prepared_paths = list(self.source_paths)
        self.accept()

    def continue_to_print(self):
        if not self.prepared_paths:
            QMessageBox.information(self, "Load photos", "Please load photos first.")
            return
        self.accept()
