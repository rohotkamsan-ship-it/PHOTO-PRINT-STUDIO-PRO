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
