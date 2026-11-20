"""Main PHOTO PRINT STUDIO PRO UI."""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QAction, QColor, QPainter, QPen, QPixmap, QImage
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QSpinBox, QDoubleSpinBox,
    QSplitter, QVBoxLayout, QWidget, QScrollArea, QGroupBox, QSizePolicy,
    QCheckBox, QColorDialog,
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
        self._pixmap_cache: dict[str, QPixmap] = {}
        self.photo_color = QColor("#dce7f3")
        self.border_enabled = False
        self.border_color = QColor("#222222")

    def set_images(self, image_paths: list[str]) -> None:
        self.image_paths = list(image_paths)
        self._pixmap_cache = {}
        for path in self.image_paths:
            if path not in self._pixmap_cache:
                self._pixmap_cache[path] = QPixmap(path)
        self.update()

    def set_cut_border(self, enabled: bool, color: QColor) -> None:
        self.border_enabled = enabled
        self.border_color = QColor(color)
        self.update()

    def set_sheet(self, width: float, height: float, placements) -> None:
        self.paper_width, self.paper_height = width, height
        self.placements = placements
        self.updateGeometry()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
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
                pixmap = self._pixmap_cache.get(self.image_paths[index % len(self.image_paths)])
                if pixmap is not None and not pixmap.isNull():
                    self._draw_fitted_photo(painter, pixmap, target)
            else:
                painter.fillRect(target, self.photo_color)
                painter.setPen(QColor("#52657a"))
                painter.drawText(target, Qt.AlignmentFlag.AlignCenter, "LOAD PHOTO")
            painter.setBrush(Qt.BrushStyle.NoBrush)
            if self.border_enabled:
                painter.setPen(QPen(self.border_color, max(1.0, scale * 0.25)))
                painter.drawRect(target)

    @staticmethod
    def _draw_fitted_photo(painter: QPainter, pixmap: QPixmap, target: QRectF) -> None:
        # Crop the source rectangle mathematically, then let QPainter scale
        # directly from the original-resolution pixmap to the output target.
        # This avoids an intermediate low-resolution pixmap and double resampling.
        source_w, source_h = pixmap.width(), pixmap.height()
        target_ratio = target.width() / max(1.0, target.height())
        source_ratio = source_w / max(1.0, source_h)
        if source_ratio > target_ratio:
            crop_w = source_h * target_ratio
            source = QRectF((source_w - crop_w) / 2, 0, crop_w, source_h)
        else:
            crop_h = source_w / target_ratio
            source = QRectF(0, (source_h - crop_h) / 2, source_w, crop_h)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setClipRect(target)
        painter.drawPixmap(target, pixmap, source)
        painter.restore()


class MainWindow(QMainWindow):
    def __init__(self, initial_images=None):
        super().__init__()
        self.setWindowTitle("PHOTO PRINT STUDIO PRO")
        self.resize(1440, 900)
        self.image_paths: list[str] = list(initial_images or [])
        self._border_color = "#222222"
        self._build_menu()
        self._build_ui()
        self._preset_changed()
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
        about_action = QAction("About PHOTO PRINT STUDIO PRO", self)
        about_action.triggered.connect(self.show_about)
        file_menu.addAction(about_action)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def show_about(self):
        QMessageBox.about(
            self,
            "About PHOTO PRINT STUDIO PRO",
            "<b>PHOTO PRINT STUDIO PRO</b><br>"
            "Professional Photo Printing<br><br>"
            "Created by <b>Mr. Sam Oun</b>"
        )

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
        self.preview.set_cut_border(False, QColor(self._border_color))
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
        creator = QLabel("Created by Mr. Sam Oun")
        creator.setObjectName("creatorCredit")
        footer.addWidget(creator)
        back_button = QPushButton("←  Back · Photo Preparation")
        back_button.clicked.connect(self.back_to_preparation)
        footer.addWidget(back_button)
        self.status = QLabel("Ready · Load a photo to begin")
        footer.addWidget(self.status, 1)
        pdf_button = QPushButton("Export PDF")
        pdf_button.clicked.connect(self.export_pdf)
        footer.addWidget(pdf_button)
        jpg_button = QPushButton("Export JPG")
        png_button = QPushButton("Export PNG")
        jpg_button.clicked.connect(lambda: self.export_raster("jpg"))
        png_button.clicked.connect(lambda: self.export_raster("png"))
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
        self._last_photo_orientation = self.photo_orientation.currentText()
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
        self.photo_w.valueChanged.connect(self._custom_photo_dimensions_changed)
        self.photo_h.valueChanged.connect(self._custom_photo_dimensions_changed)
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

        border_group = self._group("CUTTING LINE / PHOTO BORDER")
        border_layout = QVBoxLayout(border_group)
        self.border_enabled = QCheckBox("Show line around each photo")
        self.border_enabled.setChecked(False)
        self.border_enabled.toggled.connect(self._cut_border_changed)
        border_layout.addWidget(self.border_enabled)
        border_controls = QHBoxLayout()
        self.border_color_button = QPushButton("Choose line color")
        self.border_color_button.clicked.connect(self._choose_border_color)
        self.border_color_label = QLabel("#222222")
        self.border_color_label.setObjectName("helperText")
        border_controls.addWidget(self.border_color_button)
        border_controls.addWidget(self.border_color_label)
        border_layout.addLayout(border_controls)
        border_hint = QLabel("Optional cut guide. Turn it off for borderless photos.")
        border_hint.setWordWrap(True)
        border_hint.setObjectName("helperText")
        border_layout.addWidget(border_hint)
        layout.addWidget(border_group)
        self.border_color_button.setEnabled(False)
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

    def _cut_border_changed(self, enabled: bool):
        self.border_color_button.setEnabled(enabled)
        self.preview.set_cut_border(enabled, QColor(self._border_color))

    def _choose_border_color(self):
        color = QColorDialog.getColor(QColor(self._border_color), self, "Choose cutting line color")
        if color.isValid():
            self._border_color = color.name()
            self.border_color_label.setText(self._border_color)
            self.preview.set_cut_border(self.border_enabled.isChecked(), color)

    def _set_photo_dimensions(self, width: float, height: float) -> None:
        self.photo_w.blockSignals(True)
        self.photo_h.blockSignals(True)
        self.photo_w.setValue(width)
        self.photo_h.setValue(height)
        self.photo_w.blockSignals(False)
        self.photo_h.blockSignals(False)

    def _preset_changed(self, *_):
        name, unit = self.preset.currentText(), self.unit.currentText()
        if name in PHOTO_PRESETS_MM:
            width, height = photo_size(name, unit)
            if self.photo_orientation.currentText() == "Landscape":
                width, height = height, width
            self._set_photo_dimensions(width, height)
        self._last_photo_orientation = self.photo_orientation.currentText()
        self.recalculate()

    def _custom_photo_dimensions_changed(self, *_):
        # Editing either dimension switches to Custom so the selected values
        # are not silently overwritten by a preset on the next orientation change.
        if self.preset.currentText() != "Custom":
            self.preset.blockSignals(True)
            self.preset.setCurrentText("Custom")
            self.preset.blockSignals(False)
        self.recalculate()

    def _photo_orientation_changed(self, orientation: str):
        previous = getattr(self, "_last_photo_orientation", "Portrait")
        if orientation == previous:
            return
        if self.preset.currentText() == "Custom":
            width, height = self.photo_w.value(), self.photo_h.value()
            self._set_photo_dimensions(height, width)
        else:
            name, unit = self.preset.currentText(), self.unit.currentText()
            if name in PHOTO_PRESETS_MM:
                width, height = photo_size(name, unit)
                if orientation == "Landscape":
                    width, height = height, width
                self._set_photo_dimensions(width, height)
        self._last_photo_orientation = orientation
        self.recalculate()

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

    def back_to_preparation(self):
        # Reopen Step 1 with the current photo set so the user can revise
        # background removal or replace/add photos without losing their work.
        from .photo_preparation import PhotoPreparationDialog

        dialog = PhotoPreparationDialog(self, initial_images=self.image_paths)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.image_paths = list(dialog.prepared_paths)
            self.recalculate()
            self.status.setText(
                f"Returned from Photo Preparation · {len(self.image_paths)} photo(s) ready"
            )

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
            self.preview.set_cut_border(self.border_enabled.isChecked(), QColor(self._border_color))
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
            self.preview.set_cut_border(self.border_enabled.isChecked(), QColor(self._border_color))
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
                if self.border_enabled.isChecked():
                    painter.setPen(QPen(QColor(self._border_color), max(1.0, scale * 0.25)))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRect(target)
        finally:
            painter.end()
        self.status.setText(f"PDF exported: {path}")

    def export_raster(self, image_format: str):
        """Export the complete print sheet as a 300-DPI JPG or PNG image."""
        if not self.image_paths:
            QMessageBox.information(self, "No photos loaded", "Please load at least one photo before exporting.")
            return
        if not self.preview.placements:
            QMessageBox.warning(self, "No layout", "The current photo size does not fit on the selected paper.")
            return

        image_format = image_format.lower()
        extension = "jpg" if image_format in ("jpg", "jpeg") else "png"
        default_name = f"photo-sheet.{extension}"
        file_filter = "JPEG Image (*.jpg *.jpeg)" if extension == "jpg" else "PNG Image (*.png)"
        path, _ = QFileDialog.getSaveFileName(self, f"Export {extension.upper()}", default_name, file_filter)
        if not path:
            return
        if not path.lower().endswith((".jpg", ".jpeg") if extension == "jpg" else (".png",)):
            path += f".{extension}"

        dpi = 300
        width_px = max(1, round(self.preview.paper_width / 25.4 * dpi))
        height_px = max(1, round(self.preview.paper_height / 25.4 * dpi))
        image = QImage(width_px, height_px, QImage.Format.Format_RGB32)
        image.fill(QColor("#ffffff"))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        scale = dpi / 25.4
        for index, item in enumerate(self.preview.placements):
            target = QRectF(
                item.x_mm * scale, item.y_mm * scale,
                item.width_mm * scale, item.height_mm * scale
            )
            source_path = self.image_paths[index % len(self.image_paths)]
            pixmap = self.preview._pixmap_cache.get(source_path)
            if pixmap is None or pixmap.isNull():
                pixmap = QPixmap(source_path)
            if not pixmap.isNull():
                SheetPreview._draw_fitted_photo(painter, pixmap, target)
            if self.border_enabled.isChecked():
                painter.setPen(QPen(QColor(self._border_color), max(1.0, scale * 0.25)))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(target)
        painter.end()

        if extension == "jpg":
            image.setDotsPerMeterX(round(dpi / 0.0254))
            image.setDotsPerMeterY(round(dpi / 0.0254))
            saved = image.save(path, "JPG", quality=95)
        else:
            image.setDotsPerMeterX(round(dpi / 0.0254))
            image.setDotsPerMeterY(round(dpi / 0.0254))
            saved = image.save(path, "PNG")

        if not saved:
            QMessageBox.critical(self, "Export failed", f"Could not save the image file:\\n{path}")
            return
        self.status.setText(f"{extension.upper()} exported · 300 DPI · {path}")
        QMessageBox.information(self, "Export complete", f"Print sheet exported successfully:\\n{path}")

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
                    if self.border_enabled.isChecked():
                        painter.setPen(QPen(QColor(self._border_color), max(1.0, scale * 0.25)))
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.drawRect(target)
                painter.end()

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #eef2f7; }
            QMenuBar { color: #1e293b; background: #eef2f7; }
            QMenuBar::item { color: #1e293b; padding: 5px 9px; }
            QMenu { color: #1e293b; background: #ffffff; }
            QMenu::item { color: #1e293b; padding: 6px 24px; }
            #header { background: #182638; color: white; padding: 16px; font-size: 18px; font-weight: 700; }
            #creatorCredit { color: #52657a; font-size: 11px; font-weight: 700; padding: 4px 8px; }
            #previewPanel { background: #e5eaf1; border: 1px solid #d0d8e2; border-radius: 10px; }
            #sectionTitle { font-size: 16px; font-weight: 700; color: #26384d; }
            QGroupBox { font-weight: 700; color: #34465a; border: 1px solid #d2dbe6; border-radius: 8px; margin-top: 12px; padding: 12px 8px 8px; background: white; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { color: #1e293b; background: #ffffff; border: 1px solid #c8d3df; border-radius: 6px; padding: 9px 12px; font-size: 12px; font-weight: 600; }
            QPushButton:disabled { color: #64748b; background: #e8edf3; }
            QCheckBox { color: #1e293b; spacing: 8px; font-size: 12px; }
            QPushButton:hover { border-color: #397fc2; }
            #primaryButton { background: #246fc1; color: #ffffff; font-weight: 700; }
            #primaryButton:disabled { color: #ffffff; }
            QLabel { color: #30445b; font-size: 12px; } #helperText { color: #64748b; font-size: 11px; }
            QComboBox, QSpinBox, QDoubleSpinBox { background: #ffffff; color: #1e293b; border: 1px solid #b8c7d8; border-radius: 6px; padding: 6px 8px; min-height: 26px; font-size: 12px; selection-background-color: #246fc1; } QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border: 1px solid #397fc2; } QComboBox QAbstractItemView { background: #ffffff; color: #1e293b; selection-background-color: #246fc1; selection-color: #ffffff; }
        """)


