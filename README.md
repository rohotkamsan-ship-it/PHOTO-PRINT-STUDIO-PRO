# PHOTO PRINT STUDIO PRO

Windows desktop application for arranging and printing ID/passport photos on A4, A5, and custom paper.

## Current scope
- Photo presets: 2×3, 3×4, 4×6 (dimensions switch between mm and cm)
- Custom photo dimensions (mm/cm)
- Paper: A4, A5, or custom dimensions
- Centered print-sheet preview
- Auto layout, copies, margins, spacing, crop/zoom/rotation
- Export PDF/JPG/PNG and direct printing
- 300 DPI print output (with optional higher-resolution setting)

## Development
- Python 3.11+
- PySide6
- Pillow
- pytest

Install:
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Run tests:
```powershell
pytest
```

Build:
```powershell
python -m pip install -r requirements-build.txt
pyinstaller --noconfirm --clean --windowed --name "PhotoPrintStudioPro" --icon assets/app.ico main.py
```

The first milestone is a functional UI and print-layout foundation. Validate printer-specific output on the target Windows printer before production use.
