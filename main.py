from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from jarvis.ui.main_window import JarvisWindow
from jarvis.utils.logging_config import logger


def main():
    logger.info("Initializing Personal JARVIS Desktop Assistant...")
    # Enable High-DPI scaling for sharp rendering on 4K/retina Windows displays
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Personal JARVIS")
    app.setOrganizationName("JarvisAI")

    icon_path = Path(__file__).resolve().parent / "assets" / "jarvis_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    try:
        window = JarvisWindow()
        window.show()
        logger.info("Main JARVIS window displayed.")
        sys.exit(app.exec())
    except Exception as exc:
        logger.critical(f"Unhandled exception in JARVIS application: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
