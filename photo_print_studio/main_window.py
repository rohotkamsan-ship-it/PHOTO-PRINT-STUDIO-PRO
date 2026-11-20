"""Main PHOTO PRINT STUDIO PRO UI."""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QAction, QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QSpinBox, QDoubleSpinBox,
    QSplitter, QVBoxLayout, QWidget, QScrollArea, QGroupBox, QSizePolicy,
)

from .measurements import PHOTO_PRESETS_MM, PAPER_PRESETS_MM, photo_size, paper_size
from .layout_engine import calculate_layout


class SheetPreview(QWidget):
    """Centered paper preview; geometry is calculated in physical millimetres."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.paper_width = 210.0
        self.paper_height = 297.0
        self.placements = []
        self.image_paths: list[str] = []
        self.photo_color = QColor("#dce7f3")

    def set_images(self, image_paths: list[str]) -> None:
        self.image_paths = list(image_paths)
        self.update()

    def set_sheet(self, width: float, height: float, placements) -> None:
        self.paper_width, self.paper_height = width, height
        self.placements = placements
        self.updateGeometry()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = self.rect().adjusted(28, 28, -28, -28)
        available_w = max(1, area.width())
        available_h = max(1, area.height())
        # Refit the page whenever paper size, orientation, or preview area changes.
        scale = min(available_w / self.paper_width, available_h / self.paper_height)
        page_w, page_h = self.paper_width * scale, self.paper_height * scale
        page = self.rect().center()
        left, top = page.x() - page_w / 2, page.y() - page_h / 2

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 32, 48, 35))
        painter.drawRoundedRect(int(left + 4), int(top + 5), int(page_w), int(page_h), 5, 5)
        painter.setPen(QPen(QColor("#aab4c0"), 1))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(int(left), int(top), int(page_w), int(page_h), 4, 4)
        painter.setPen(QPen(QColor("#9aa8b8"), 1, Qt.PenStyle.DashLine))
        for index, item in enumerate(self.placements):
            x = left + item.x_mm * scale
            y = top + item.y_mm * scale
            w, h = item.width_mm * scale, item.height_mm * scale
            target = QRectF(x, y, w, h)
            if self.image_paths:
                pixmap = QPixmap(self.image_paths[index % len(self.image_paths)])
                if not pixmap.isNull():
                    self._draw_fitted_photo(painter, pixmap, target)
            else:
                painter.fillRect(target, self.photo_color)
                painter.setPen(QColor("#52657a"))
                painter.drawText(target, Qt.AlignmentFlag.AlignCenter, "LOAD PHOTO")
            painter.setPen(QPen(QColor("#9aa8b8"), 1, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(target)

    @staticmethod
    def _draw_fitted_photo(painter: QPainter, pixmap: QPixmap, target: QRectF) -> None:
        tw, th = max(1, int(target.width())), max(1, int(target.height()))
        scaled = pixmap.scaled(tw, th, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
        sx = max(0, (scaled.width() - tw) // 2)
        sy = max(0, (scaled.height() - th) // 2)
        source = scaled.rect().adjusted(sx, sy, sx - (scaled.width() - tw), sy - (scaled.height() - th))
        painter.save()
        painter.setClipRect(target)
        painter.drawPixmap(target.toRect(), scaled, source)
        painter.restore()


class MainWindow(QMainWindow):
    def __init__(self, initial_images=None):
        super().__init__()
        self.setWindowTitle("PHOTO PRINT STUDIO PRO")
        self.resize(1440, 900)
        self.image_paths: list[str] = list(initial_images or [])
        self._build_menu()
        self._build_ui()
        self._apply_style()
        self.recalculate()
        if self.image_paths:
            self.status.setText(f"{len(self.image_paths)} prepared photo(s) ready for print layout")

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("File")
        open_action = QAction("Load Images…", self)
        open_action.triggered.connect(self.load_images)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _build_ui(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)
        header = QLabel("PHOTO PRINT STUDIO PRO  |  Professional Photo Printing")
        header.setObjectName("header")
        root_layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._left_panel())

        center = QFrame()
        center.setObjectName("previewPanel")
        center_layout = QVBoxLayout(center)
        preview_header = QHBoxLayout()
        title = QLabel("PRINT PREVIEW")
        title.setObjectName("sectionTitle")
        self.page_info = QLabel("A4 · 300 DPI")
        preview_header.addWidget(title)
        preview_header.addStretch()
        preview_header.addWidget(self.page_info)
        center_layout.addLayout(preview_header)

        preview_scroll = QScrollArea()
        preview_scroll.setWidgetResizable(True)
        self.preview = SheetPreview()
        preview_scroll.setWidget(self.preview)
        center_layout.addWidget(preview_scroll, 1)
        splitter.addWidget(center)
        splitter.addWidget(self._right_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([280, 880, 280])
        root_layout.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.status = QLabel("Ready · Load a photo to begin")
        footer.addWidget(self.status, 1)
        pdf_button = QPushButton("Export PDF")
        pdf_button.clicked.connect(self.export_pdf)
        footer.addWidget(pdf_button)
        jpg_button = QPushButton("Export JPG")
        png_button = QPushButton("Export PNG")
        jpg_button.setEnabled(False)
        png_button.setEnabled(False)
        footer.addWidget(jpg_button)
        footer.addWidget(png_button)
        print_button = QPushButton("Print")
        print_button.setObjectName("primaryButton")
        print_button.clicked.connect(self.print_sheet)
        footer.addWidget(print_button)
        root_layout.addLayout(footer)
        self.setCentralWidget(root)

    def _group(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setFlat(False)
        return group

    def _left_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(240)
        layout = QVBoxLayout(panel)
        load = QPushButton("＋  Load Images")
        load.setMinimumHeight(42)
        load.clicked.connect(self.load_images)
        layout.addWidget(load)
        load_hint = QLabel("Select one or more JPG, PNG, TIFF or WEBP photos to begin.")
        load_hint.setWordWrap(True)
        load_hint.setObjectName("helperText")
        layout.addWidget(load_hint)

        photo_group = self._group("PHOTO SIZE")
        form = QFormLayout(photo_group)
        self.preset = QComboBox()
        self.preset.addItems(["2x3", "3x4", "4x6", "Custom"])
        self.preset.setCurrentText("3x4")
        self.unit = QComboBox()
        self.unit.addItems(["mm", "cm"])
        self.photo_orientation = QComboBox()
        self.photo_orientation.addItems(["Portrait", "Landscape"])
        self.photo_w = QDoubleSpinBox()
        self.photo_h = QDoubleSpinBox()
        for spin in (self.photo_w, self.photo_h):
            spin.setRange(1, 1000)
            spin.setDecimals(1)
        form.addRow("Preset", self.preset)
        form.addRow("Unit", self.unit)
        form.addRow("Orientation", self.photo_orientation)
        form.addRow("Width", self.photo_w)
        form.addRow("Height", self.photo_h)
        self.preset.currentTextChanged.connect(self._preset_changed)
        self.unit.currentTextChanged.connect(self._preset_changed)
        self.photo_orientation.currentTextChanged.connect(self._photo_orientation_changed)
        self.photo_w.valueChanged.connect(self.recalculate)
        self.photo_h.valueChanged.connect(self.recalculate)
        photo_hint = QLabel("Choose a standard photo size or enter custom width and height. Unit applies to both dimensions.")
        photo_hint.setWordWrap(True)
        photo_hint.setObjectName("helperText")
        form.addRow(photo_hint)
        layout.addWidget(photo_group)

        copies_group = self._group("COPIES & SPACING")
        copies_form = QFormLayout(copies_group)
        self.copies = QSpinBox()
        self.copies.setRange(1, 999)
        self.copies.setValue(1)
        self.margin = QDoubleSpinBox()
        self.margin.setRange(0, 50)
        self.margin.setValue(5)
        self.spacing = QDoubleSpinBox()
        self.spacing.setRange(0, 30)
        self.spacing.setValue(3)
        copies_form.addRow("Copies per photo", self.copies)
        copies_form.addRow("Margin (mm)", self.margin)
        copies_form.addRow("Spacing (mm)", self.spacing)
        for control in (self.copies, self.margin, self.spacing):
            control.valueChanged.connect(self.recalculate)
        layout.addWidget(copies_group)
        layout.addStretch()
        return panel

    def _right_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(240)
        layout = QVBoxLayout(panel)
        paper_group = self._group("PAPER SETTINGS")
        form = QFormLayout(paper_group)
        self.paper = QComboBox()
        self.paper.addItems(["A4", "A5", "Custom"])
        self.orientation = QComboBox()
        self.orientation.addItems(["Portrait", "Landscape"])
        self.paper_w = QDoubleSpinBox()
        self.paper_h = QDoubleSpinBox()
        self.paper_w.setValue(210)
        self.paper_h.setValue(297)
        for spin in (self.paper_w, self.paper_h):
            spin.setRange(20, 2000)
            spin.setDecimals(1)
        self.paper.currentTextChanged.connect(self._paper_changed)
        self.orientation.currentTextChanged.connect(self.recalculate)
        self.paper_w.valueChanged.connect(self.recalculate)
        self.paper_h.valueChanged.connect(self.recalculate)
        form.addRow("Paper", self.paper)
        form.addRow("Orientation", self.orientation)
        form.addRow("Custom width (mm)", self.paper_w)
        form.addRow("Custom height (mm)", self.paper_h)
        paper_hint = QLabel("Choose the paper size and page direction. Select Custom for special paper dimensions.")
        paper_hint.setWordWrap(True)
        paper_hint.setObjectName("helperText")
        form.addRow(paper_hint)
        layout.addWidget(paper_group)

        output_group = self._group("OUTPUT")
        output_layout = QVBoxLayout(output_group)
        output_layout.addWidget(QLabel("Resolution: 300 DPI"))
        output_layout.addWidget(QLabel("Output: PDF / JPG / PNG"))
        output_layout.addWidget(QLabel("Preview is a layout simulation until a photo is loaded."))
        layout.addWidget(output_group)
        layout.addStretch()
        return panel

    def _preset_changed(self, *_):
        name, unit = self.preset.currentText(), self.unit.currentText()
        if name in PHOTO_PRESETS_MM:
            width, height = photo_size(name, unit)
            if self.photo_orientation.currentText() == "Landscape":
                width, height = height, width
            self.photo_w.blockSignals(True)
            self.photo_h.blockSignals(True)
            self.photo_w.setValue(width)
            self.photo_h.setValue(height)
            self.photo_w.blockSignals(False)
            self.photo_h.blockSignals(False)
        self.recalculate()

    def _photo_orientation_changed(self, orientation: str):
        # Presets are defined in portrait dimensions; custom dimensions are swapped
        # so the selected orientation always matches the displayed width and height.
        if self.preset.currentText() == "Custom":
            width = self.photo_w.value()
            height = self.photo_h.value()
            self.photo_w.blockSignals(True)
            self.photo_h.blockSignals(True)
            self.photo_w.setValue(height)
            self.photo_h.setValue(width)
            self.photo_w.blockSignals(False)
            self.photo_h.blockSignals(False)
            self.recalculate()
        else:
            self._preset_changed()

    def _paper_changed(self, name: str):
        if name in PAPER_PRESETS_MM:
            w, h = paper_size(name)
            self.paper_w.blockSignals(True)
            self.paper_h.blockSignals(True)
            self.paper_w.setValue(w)
            self.paper_h.setValue(h)
            self.paper_w.blockSignals(False)
            self.paper_h.blockSignals(False)
        self.recalculate()

    def load_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Load Photos", "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff)"
        )
        if paths:
            self.image_paths = paths
            self.status.setText(f"{len(paths)} image(s) loaded")
            self.recalculate()

    def recalculate(self, *_):
        try:
            pw, ph = self.paper_w.value(), self.paper_h.value()
            if self.orientation.currentText() == "Landscape":
                pw, ph = ph, pw
            unit = self.unit.currentText()
            factor = 10.0 if unit == "cm" else 1.0
            photo_w, photo_h = self.photo_w.value() * factor, self.photo_h.value() * factor
            # Copies means copies per loaded image. At the default of 1,
            # every loaded photo is placed once, in row-major order.
            requested_slots = max(1, len(self.image_paths)) * self.copies.value()
            placements = calculate_layout(
                pw, ph, photo_w, photo_h, requested_slots,
                self.margin.value(), self.spacing.value()
            )
            self.preview.set_sheet(pw, ph, placements)
            self.preview.set_images(self.image_paths)
            orientation = self.orientation.currentText()
            self.page_info.setText(
                f"{self.paper.currentText()} · {orientation} · "
                f"{pw:g} × {ph:g} mm · {len(placements)} photos / page · 300 DPI"
            )
            if self.image_paths:
                self.status.setText(
                    f"{len(self.image_paths)} photo(s) · {self.copies.value()} copy/copies each · "
                    f"{len(placements)} of {requested_slots} placed on this sheet"
                )
        except ValueError as error:
            self.preview.set_sheet(self.paper_w.value(), self.paper_h.value(), [])
            self.preview.set_images(self.image_paths)
            self.status.setText(str(error))


    def export_pdf(self):
        from PySide6.QtGui import QPageLayout, QPageSize
        from PySide6.QtPrintSupport import QPrinter
        path, _ = QFileDialog.getSaveFileName(self, "Export Print Sheet", "photo-sheet.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        printer.setResolution(300)
        page_size = QPageSize(QPageSize.PageSizeId.A4 if self.paper.currentText() == "A4" else QPageSize.PageSizeId.A5)
        printer.setPageSize(page_size)
        printer.setPageOrientation(QPageLayout.Orientation.Portrait if self.orientation.currentText() == "Portrait" else QPageLayout.Orientation.Landscape)
        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Export failed", "Could not create the PDF file.")
            return
        try:
            rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            scale = min(rect.width() / self.preview.paper_width, rect.height() / self.preview.paper_height)
            page_w = self.preview.paper_width * scale
            page_h = self.preview.paper_height * scale
            left = rect.x() + (rect.width() - page_w) / 2
            top = rect.y() + (rect.height() - page_h) / 2
            for index, item in enumerate(self.preview.placements):
                x, y = left + item.x_mm * scale, top + item.y_mm * scale
                w, h = item.width_mm * scale, item.height_mm * scale
                target = QRectF(x, y, w, h)
                if self.image_paths:
                    pixmap = QPixmap(self.image_paths[index % len(self.image_paths)])
                    if not pixmap.isNull():
                        SheetPreview._draw_fitted_photo(painter, pixmap, target)
                painter.setPen(QPen(QColor("#8b98a8"), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(target)
        finally:
            painter.end()
        self.status.setText(f"PDF exported: {path}")

    def print_sheet(self):
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setResolution(300)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            painter = QPainter()
            if painter.begin(printer):
                rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                scale = min(rect.width() / self.preview.paper_width, rect.height() / self.preview.paper_height)
                page_w = self.preview.paper_width * scale
                page_h = self.preview.paper_height * scale
                left = rect.x() + (rect.width() - page_w) / 2
                top = rect.y() + (rect.height() - page_h) / 2
                for index, item in enumerate(self.preview.placements):
                    x, y = left + item.x_mm * scale, top + item.y_mm * scale
                    w, h = item.width_mm * scale, item.height_mm * scale
                    target = QRectF(x, y, w, h)
                    if self.image_paths:
                        pixmap = QPixmap(self.image_paths[index % len(self.image_paths)])
                        if not pixmap.isNull():
                            SheetPreview._draw_fitted_photo(painter, pixmap, target)
                    painter.setPen(QPen(QColor("#8b98a8"), 2))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRect(target)
                painter.end()

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #eef2f7; }
            #header { background: #182638; color: white; padding: 16px; font-size: 18px; font-weight: 700; }
            #previewPanel { background: #e5eaf1; border: 1px solid #d0d8e2; border-radius: 10px; }
            #sectionTitle { font-size: 16px; font-weight: 700; color: #26384d; }
            QGroupBox { font-weight: 700; color: #34465a; border: 1px solid #d2dbe6; border-radius: 8px; margin-top: 12px; padding: 12px 8px 8px; background: white; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { background: #ffffff; border: 1px solid #c8d3df; border-radius: 6px; padding: 9px 12px; }
            QPushButton:hover { border-color: #397fc2; }
            #primaryButton { background: #246fc1; color: white; font-weight: 700; }
            QLabel { color: #30445b; font-size: 12px; } #helperText { color: #64748b; font-size: 11px; }
            QComboBox, QSpinBox, QDoubleSpinBox { background: #ffffff; color: #1e293b; border: 1px solid #b8c7d8; border-radius: 6px; padding: 6px 8px; min-height: 26px; font-size: 12px; selection-background-color: #246fc1; } QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border: 1px solid #397fc2; } QComboBox QAbstractItemView { background: #ffffff; color: #1e293b; selection-background-color: #246fc1; selection-color: #ffffff; }
        """)


