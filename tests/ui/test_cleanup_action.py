import pytest

from app.ui.main_window import MainWindow


@pytest.mark.parametrize("has_project", [False, True])
def test_file_menu_has_no_cleanup_or_deletion_action(qtbot, has_project):
    window = MainWindow()
    qtbot.addWidget(window)
    if has_project:
        window.continue_button.click()
    file_menu = window.menuBar().actions()[0].menu()
    assert [action.text() for action in file_menu.actions()] == [
        "Nova vistoria", "Abrir vistoria existente", "Salvar", "Recuperar backup",
    ]
