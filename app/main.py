"""Application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main() -> None:
    """Show the main window and run the Qt event loop."""
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("VistoriaApp")
    window = MainWindow()
    window.show()
    application.exec()


if __name__ == "__main__":
    main()
