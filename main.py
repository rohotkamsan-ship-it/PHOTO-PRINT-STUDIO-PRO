"""PHOTO PRINT STUDIO PRO - Windows desktop application entry point."""
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from photo_print_studio.donate_dialog import DonateDialog
from photo_print_studio.main_window import MainWindow
from photo_print_studio.photo_preparation import PhotoPreparationDialog


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PHOTO PRINT STUDIO PRO")
    app.setOrganizationName("RohotKamsan")

    # Donation is optional: users can continue without donating.
    donation = DonateDialog()
    if donation.exec() != donation.DialogCode.Accepted:
        return 0

    preparation = PhotoPreparationDialog()
    if preparation.exec() != preparation.DialogCode.Accepted:
        return 0
    window = MainWindow(initial_images=preparation.prepared_paths)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
