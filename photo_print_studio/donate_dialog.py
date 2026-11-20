"""Voluntary startup donation dialog for PHOTO PRINT STUDIO PRO."""
from __future__ import annotations

import base64

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout

_QR_PNG_BASE64 = "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"


class DonateDialog(QDialog):
    """Show the supplied donation QR code before entering the application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Support PHOTO PRINT STUDIO PRO")
        self.setModal(True)
        self.setFixedSize(440, 610)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("SUPPORT THE DEVELOPER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 21px; font-weight: 800; color: #183653;")
        layout.addWidget(title)

        subtitle = QLabel("Scan the QR code below to donate")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #52657a;")
        layout.addWidget(subtitle)

        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_label.setFixedSize(340, 340)
        qr_label.setStyleSheet("background: white; border: 1px solid #d7e0e9; border-radius: 12px;")
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(_QR_PNG_BASE64), "PNG")
        if not pixmap.isNull():
            qr_label.setPixmap(pixmap.scaled(
                320, 320, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            ))
        else:
            qr_label.setText("QR code unavailable")
        layout.addWidget(qr_label, 0, Qt.AlignmentFlag.AlignHCenter)

        message = QLabel(
            "Your support helps us improve this software.\n"
            "Thank you for your kindness!"
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 13px; color: #52657a;")
        layout.addWidget(message)

        creator = QLabel("Created by Mr. Sam Oun")
        creator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        creator.setStyleSheet("font-size: 12px; font-weight: 700; color: #52657a;")
        layout.addWidget(creator)

        buttons = QHBoxLayout()
        buttons.addStretch()
        continue_button = QPushButton("Continue to Application")
        continue_button.setMinimumHeight(40)
        continue_button.setStyleSheet(
            "QPushButton { color: white; background: #246fc1; border: 0; "
            "border-radius: 7px; padding: 8px 18px; font-weight: 700; }"
            "QPushButton:hover { background: #1c5e9f; }"
        )
        continue_button.clicked.connect(self.accept)
        buttons.addWidget(continue_button)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.setStyleSheet("QDialog { background: #f4f7fb; }")
