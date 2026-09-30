import pytest
from PySide6.QtWidgets import QApplication

from app.main import main
from app.ui.main_window import MainWindow


def test_main_shows_window_and_enters_event_loop(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch,
) -> None:
    entered = []

    def exec_loop() -> int:
        windows = [w for w in qapp.topLevelWidgets() if isinstance(w, MainWindow) and w.isVisible()]
        assert len(windows) == 1
        entered.append(True)
        windows[0].close()
        return 0

    monkeypatch.setattr(QApplication, "exec", staticmethod(exec_loop))
    main()
    assert entered == [True]
