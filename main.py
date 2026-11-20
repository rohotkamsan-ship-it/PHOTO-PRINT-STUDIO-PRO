"""PHOTO PRINT STUDIO PRO - Windows desktop application entry point."""
from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path

from PySide6.QtWidgets import QApplication

from photo_print_studio.donate_dialog import DonateDialog
from photo_print_studio.main_window import MainWindow
from photo_print_studio.photo_preparation import PhotoPreparationDialog


def _run_ai_packaging_self_test() -> int:
    """Verify rembg and its runtime dependencies inside the frozen application."""
    configured_log = os.environ.get("PHOTO_PRINT_AI_TEST_LOG")
    log_path = Path(configured_log) if configured_log else (
        Path(tempfile.gettempdir()) / "PhotoPrintStudioPro-ai-self-test.log"
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from rembg import new_session, remove  # noqa: F401
        import onnxruntime  # noqa: F401

        log_path.write_text("AI packaging self-test: PASS\\n", encoding="utf-8")
        return 0
    except Exception:
        log_path.write_text(
            "AI packaging self-test: FAIL\\n" + traceback.format_exc(),
            encoding="utf-8",
        )
        return 1


def main() -> int:
    if "--self-test-ai" in sys.argv:
        return _run_ai_packaging_self_test()

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
