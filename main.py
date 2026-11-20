"""PHOTO PRINT STUDIO PRO - Windows desktop application entry point."""
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from photo_print_studio.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PHOTO PRINT STUDIO PRO")
    app.setOrganizationName("RohotKamsan")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
