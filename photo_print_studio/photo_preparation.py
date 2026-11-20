"""Photo preparation step shown before print layout."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QFileDialog, QComboBox, QColorDialog, QMessageBox, QProgressDialog,
    QGroupBox, QApplication, QSizePolicy, QWidget,
)

from .background_tools import prepare_image


class ImagePreviewLabel(QLabel):
    """Keep the original image and rescale it whenever the preview area changes."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._source_pixmap = QPixmap()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_image(self, pixmap: QPixmap):
        self._source_pixmap = pixmap
        self._update_scaled_pixmap()

    def clear_image(self, message: str = ""):
        self._source_pixmap = QPixmap()
        self.setPixmap(QPixmap())
        self.setText(message)

    def _update_scaled_pixmap(self):
        if self._source_pixmap.isNull():
            return
        target = self.contentsRect().size()
        if target.width() < 2 or target.height() < 2:
            return
        scaled = self._source_pixmap.scaled(
            target, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()


class PhotoPreparationDialog(QDialog):
    """Load photos, optionally remove their backgrounds, and choose a fill color."""

    def __init__(self, parent=None, initial_images=None):
        super().__init__(parent)
        self.setWindowTitle("Photo Preparation · PHOTO PRINT STUDIO PRO")
        self.resize(1180, 780)
        self.setMinimumSize(900, 620)
        self.source_paths: list[str] = []
        self.prepared_paths: list[str] = []
        self.background_color = "#ffffff"
        initial_images = list(initial_images or [])
        self.source_paths = list(initial_images)
        self.prepared_paths = list(initial_images)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(12)

        heading_row = QHBoxLayout()
        heading = QLabel("STEP 1  ·  PHOTO PREPARATION")
        heading.setObjectName("pageTitle")
        heading_row.addWidget(heading)
        heading_row.addStretch()
        self.photo_count = QLabel("0 photos loaded")
        self.photo_count.setObjectName("countBadge")
        heading_row.addWidget(self.photo_count)
        root.addLayout(heading_row)

        subtitle = QLabel(
            "Load your photos, select a photo, remove its background if needed, "
            "then continue to the print layout."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(16)

        # Left: image queue and clear load action.
        left_panel = QGroupBox("PHOTO QUEUE")
        left_panel.setObjectName("panel")
        left_panel.setMinimumWidth(260)
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(14, 18, 14, 14)
        left_layout.setSpacing(10)

        load = QPushButton("＋  Load Photos")
        load.setObjectName("loadButton")
        load.setMinimumHeight(44)
        load.clicked.connect(self.load_images)
        left_layout.addWidget(load)

        self.files = QListWidget()
        self.files.setObjectName("photoList")
        self.files.setSpacing(4)
        self.files.currentRowChanged.connect(self._show_preview)
        left_layout.addWidget(self.files, 1)

        self.selection_info = QLabel("No photo selected")
        self.selection_info.setObjectName("muted")
        self.selection_info.setWordWrap(True)
        left_layout.addWidget(self.selection_info)

        remove = QPushButton("✂  Remove Background · Free AI")
        remove.setObjectName("removeButton")
        remove.setMinimumHeight(44)
        remove.clicked.connect(self.remove_backgrounds)
        left_layout.addWidget(remove)

        skip = QPushButton("Keep Original Photos")
        skip.setObjectName("secondaryButton")
        skip.clicked.connect(self.skip_editing)
        left_layout.addWidget(skip)
        body.addWidget(left_panel, 0)

        # Right: large, contained preview and background controls.
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        preview_group = QGroupBox("PHOTO PREVIEW")
        preview_group.setObjectName("panel")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(12, 18, 12, 12)
        self.preview = ImagePreviewLabel("Load photos to see a preview")
        self.preview.setObjectName("imagePreview")
        self.preview.setMinimumSize(400, 390)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout.addWidget(self.preview, 1)
        right_layout.addWidget(preview_group, 1)

        background_group = QGroupBox("BACKGROUND SETTINGS")
        background_group.setObjectName("panel")
        bg_layout = QHBoxLayout(background_group)
        bg_layout.setContentsMargins(14, 18, 14, 14)
        bg_layout.setSpacing(12)

        bg_text = QVBoxLayout()
        bg_title = QLabel("Background after removal")
        bg_title.setObjectName("fieldTitle")
        bg_hint = QLabel("Choose the color to apply when you click Remove Background.")
        bg_hint.setObjectName("muted")
        bg_hint.setWordWrap(True)
        bg_text.addWidget(bg_title)
        bg_text.addWidget(bg_hint)
        bg_layout.addLayout(bg_text, 1)

        self.background = QComboBox()
        self.background.addItems(["Transparent", "White", "Blue", "Light Blue", "Red", "Custom color"])
        self.background.setMinimumWidth(170)
        self.background.currentTextChanged.connect(self._background_changed)
        bg_layout.addWidget(self.background)

        self.custom_button = QPushButton("Choose Color")
        self.custom_button.setObjectName("secondaryButton")
        self.custom_button.clicked.connect(self._choose_color)
        self.custom_button.setEnabled(False)
        bg_layout.addWidget(self.custom_button)
        right_layout.addWidget(background_group)
        body.addWidget(right_panel, 1)
        root.addLayout(body, 1)

        footer = QHBoxLayout()
        footer.setSpacing(10)
        note = QLabel("Tip: Background editing is optional. Original photos can be used as-is.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        footer.addWidget(note, 1)

        next_button = QPushButton("Next · Print Layout  →")
        next_button.setObjectName("primaryButton")
        next_button.setMinimumHeight(48)
        next_button.setMinimumWidth(210)
        next_button.clicked.connect(self.continue_to_print)
        footer.addWidget(next_button)
        root.addLayout(footer)

        if initial_images:
            self.files.addItems([Path(path).name for path in initial_images])
            self.photo_count.setText(f"{len(initial_images)} photo(s) loaded")
            self.files.setCurrentRow(0)
            self._show_preview(0)

        self.setStyleSheet("""
            QDialog { background: #f3f6fb; }
            QLabel { color: #26384d; background: transparent; }
            QLabel#pageTitle { color: #173653; font-size: 23px; font-weight: 800; }
            QLabel#subtitle { color: #5c6f84; font-size: 13px; padding-bottom: 2px; }
            QLabel#countBadge { color: #1d5f96; background: #e5f1fb; border: 1px solid #c8dff2;
                                border-radius: 12px; padding: 6px 12px; font-weight: 700; }
            QLabel#muted { color: #64748b; font-size: 12px; }
            QLabel#fieldTitle { color: #243b53; font-size: 13px; font-weight: 700; }
            QGroupBox#panel { background: #ffffff; color: #28425d; font-weight: 800;
                              border: 1px solid #d4deea; border-radius: 10px;
                              margin-top: 8px; padding-top: 8px; }
            QGroupBox#panel::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
            QListWidget#photoList { background: #f8fafc; color: #26384d;
                                    border: 1px solid #d8e1eb; border-radius: 8px;
                                    padding: 6px; outline: 0; }
            QListWidget#photoList::item { padding: 10px 8px; border-radius: 5px; }
            QListWidget#photoList::item:selected { background: #e2effb; color: #124f80; }
            QLabel#imagePreview { background: #edf2f8; color: #718096;
                                  border: 1px dashed #a9bacd; border-radius: 8px;
                                  padding: 8px; }
            QPushButton { color: #26384d; background: #ffffff; border: 1px solid #c8d4e1;
                          border-radius: 7px; padding: 10px 13px; font-size: 12px; font-weight: 700; }
            QPushButton:hover { background: #f0f6fc; border-color: #7aa6cf; }
            QPushButton:disabled { color: #9aa8b8; background: #f1f4f7; }
            QPushButton#loadButton { color: #ffffff; background: #285f91; border-color: #285f91; }
            QPushButton#loadButton:hover { background: #1e507e; }
            QPushButton#removeButton { color: #ffffff; background: #16806a; border-color: #16806a; }
            QPushButton#removeButton:hover { background: #116b59; }
            QPushButton#primaryButton { color: #ffffff; background: #1769aa; border-color: #1769aa;
                                        font-size: 13px; }
            QPushButton#primaryButton:hover { background: #12598f; }
            QPushButton#secondaryButton { background: #f8fafc; }
            QComboBox { color: #26384d; background: #ffffff; border: 1px solid #c8d4e1;
                        border-radius: 7px; padding: 9px 10px; min-height: 22px; }
            QComboBox QAbstractItemView { color: #26384d; background: #ffffff;
                                          selection-background-color: #dcecf9; }
        """)

    def load_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Load Photos", "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff)"
        )
        if not paths:
            return
        self.source_paths = list(paths)
        self.prepared_paths = list(paths)
        self.files.clear()
        self.files.addItems([Path(path).name for path in paths])
        self.photo_count.setText(f"{len(paths)} photo(s) loaded")
        self.files.setCurrentRow(0)
        self._show_preview(0)

    def _show_preview(self, row: int):
        if row < 0 or row >= len(self.prepared_paths):
            self.preview.clear_image("Load photos to see a preview")
            self.selection_info.setText("No photo selected")
            return
        path = self.prepared_paths[row]
        pix = QPixmap(path)
        if pix.isNull():
            self.preview.clear_image("Unable to preview this image")
        else:
            self.preview.setText("")
            self.preview.set_image(pix)
        self.selection_info.setText(f"Photo {row + 1} of {len(self.prepared_paths)}  ·  {Path(path).name}")

    def _background_changed(self, value: str):
        self.custom_button.setEnabled(value == "Custom color")

    def _choose_color(self):
        color = QColorDialog.getColor(QColor(self.background_color), self, "Choose background color")
        if color.isValid():
            self.background_color = color.name()
            self.custom_button.setText(f"Color: {self.background_color}")

    def remove_backgrounds(self):
        if not self.source_paths:
            QMessageBox.information(self, "Load photos", "Please load at least one photo first.")
            return
        choice = self.background.currentText()
        colors = {
            "White": "#ffffff", "Blue": "#1677d2", "Light Blue": "#9fd5f5",
            "Red": "#d92736", "Custom color": self.background_color, "Transparent": None,
        }
        color = colors.get(choice)
        output_dir = Path.home() / "Pictures" / "PHOTO_PRINT_STUDIO_PRO" / "Prepared"
        output_dir.mkdir(parents=True, exist_ok=True)
        progress = QProgressDialog(
            "Removing photo backgrounds with the free AI model…", "Cancel",
            0, len(self.source_paths), self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        results: list[str] = []
        try:
            for index, source in enumerate(self.source_paths):
                if progress.wasCanceled():
                    break
                target = output_dir / f"{Path(source).stem}_prepared.png"
                progress.setValue(index)
                QApplication.processEvents()
                results.append(prepare_image(source, str(target), color))
            progress.setValue(len(self.source_paths))
        except Exception as exc:
            QMessageBox.critical(self, "Background removal failed", str(exc))
            return

        # Keep untouched originals for any items skipped when the user cancels.
        if results:
            result_by_source = dict(zip(self.source_paths, results))
            self.prepared_paths = [result_by_source.get(path, path) for path in self.source_paths]
            self.files.setCurrentRow(0)
            QMessageBox.information(
                self, "Background removal complete",
                f"Prepared {len(results)} of {len(self.source_paths)} photo(s).\nSaved in:\n{output_dir}"
            )

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
