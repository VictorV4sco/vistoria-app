from copy import deepcopy
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication

from app.models.report import Report
from app.models.section import Section
from app.services.cleanup_service import CleanupService
from app.services.project_service import ProjectService
from app.ui.main_window import MainWindow
from app.ui.section_photos_widget import SectionPhotosWidget


@pytest.fixture
def window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    return window


def test_photo_tooltip_matches_managed_storage(qtbot, tmp_path):
    for directory in (None, tmp_path):
        widget = SectionPhotosWidget(Section("Sala"), directory)
        qtbot.addWidget(widget)
        assert "Selecione a pasta" not in widget.add_button.toolTip()
        assert widget.add_button.toolTip() == (
            "Crie ou abra uma vistoria para adicionar fotos." if directory is None
            else "Adicione fotos a este ambiente."
        )


@pytest.mark.parametrize("action", ["create", "open"])
def test_file_menu_availability(window, action):
    actions = {action.text(): action for action in window.menuBar().actions()[0].menu().actions()}
    assert "Executar limpeza" not in actions
    for label in ("Nova vistoria", "Abrir vistoria existente"):
        assert actions[label].isEnabled()
    for label in ("Salvar", "Recuperar backup"):
        assert not actions[label].isEnabled()
    if action == "open":
        directory = window.app_paths.projects_root / "existing"
        ProjectService.save(Report(title="Casa"), directory)
        window.start_page.open_button.click()
    else:
        window.continue_button.click()
    for item in actions.values():
        assert item.isEnabled()


def test_window_title_updates_on_binding_and_editing(window, tmp_path):
    assert window.windowTitle() == "VistoriaApp"
    for report, expected in ((Report(title="Casa"), "Casa"),
                             (Report(title="  ", report_type="Final"), "Final"),
                             (Report(title="Apartamento"), "Apartamento")):
        window._set_project(report, tmp_path / "project")
        assert window.windowTitle() == f"VistoriaApp — {expected}"
        assert window.statusBar().currentMessage() == f"Vistoria aberta: {expected}"
        assert str(tmp_path) not in window.windowTitle()
    window.form_page.title_field.setText("Título atualizado")
    assert window.windowTitle() == "VistoriaApp — Título atualizado"
    assert window.statusBar().currentMessage() == "Alterações não salvas"
    window.save_action.trigger()
    assert window.statusBar().currentMessage() == "Projeto salvo"


def test_navigation_and_rebinding_do_not_mark_dirty(window):
    window.continue_button.click()
    before = deepcopy(window.report)
    pages = (window.form_page, window.parties_page, window.environments_page, window.review_page)
    for page in pages:
        changed = Mock()
        page.changed.connect(changed)
        if page in (window.environments_page, window.review_page):
            page.set_report(window.report, window.project_directory)
        else:
            page.set_report(window.report)
        changed.assert_not_called()
    for navigate in (window._show_parties, window._show_environments, window._show_review,
                     window._show_environments, window._show_parties, window._show_form,
                     window._show_start):
        navigate()
        assert not window.autosave_service.is_dirty
        assert not window.debounce_timer.isActive()
        assert window.report == before


@pytest.mark.parametrize("status", ["Alterações não salvas", "Salvo automaticamente",
                                   "Projeto salvo", "Backup restaurado com sucesso"])
def test_startup_preserves_project_status_without_cleanup(qtbot, monkeypatch, status):
    run = Mock()
    monkeypatch.setattr(CleanupService, "run", run)
    window = MainWindow()
    qtbot.addWidget(window)
    window.statusBar().showMessage(status)
    QCoreApplication.processEvents()
    run.assert_not_called()
    assert window.statusBar().currentMessage() == status
