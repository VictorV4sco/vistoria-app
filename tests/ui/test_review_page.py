from copy import deepcopy
from datetime import date

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.models.complementary_information import ComplementaryInformation
from app.models.party import Party
from app.models.photo import Photo
from app.models.property import Property
from app.models.report import Report
from app.models.section import Section
from app.services.document_generator import DocumentGenerator
from app.ui.main_window import MainWindow
from app.ui.review_page import ReviewPage

FIELDS = ("delivered_keys", "energy_meter", "consumer_unit", "general_notes", "issue_location")


@pytest.fixture
def report():
    return Report(
        title="Vistoria da casa", inspection_date=date(2026, 9, 30), inspector_name="Ana",
        property=Property(property_type="Casa", address="Rua A", number="10"),
        landlord=Party(name="Bruno"), tenant=Party(name="Carla"),
        complementary_information=ComplementaryInformation("2", "123", "456", "Notas", "Rio"),
    )


@pytest.fixture
def page(qtbot, report, tmp_path):
    page = ReviewPage()
    qtbot.addWidget(page)
    page.set_report(report, tmp_path / "project")
    page.show()
    return page


@pytest.fixture
def dialogs(monkeypatch, tmp_path):
    calls = {"save": [], "generate": [], "warning": [], "success": []}

    def save(*args):
        calls["save"].append(args)
        return str(tmp_path / "project" / "relatorios" / "relatorio-vistoria.docx"), ""

    monkeypatch.setattr(QFileDialog, "getSaveFileName", save)
    monkeypatch.setattr(DocumentGenerator, "generate", lambda *args: calls["generate"].append(args))
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: calls["warning"].append(args))
    monkeypatch.setattr(QMessageBox, "information", lambda *args: calls["success"].append(args))
    return calls


def test_load_existing_values_without_mutation(page, report):
    before = deepcopy(report)
    for name in FIELDS:
        field = getattr(page, f"{name}_field")
        value = field.toPlainText() if name == "general_notes" else field.text()
        assert value == getattr(report.complementary_information, name)
    assert report == before


@pytest.mark.parametrize("name", FIELDS)
def test_edit_updates_same_complementary_information(page, report, name):
    original = report.complementary_information
    field = getattr(page, f"{name}_field")
    if name == "general_notes":
        field.setPlainText("Texto\nNovo")
        expected = "Texto\nNovo"
    else:
        field.setText("Novo")
        expected = "Novo"
    assert report.complementary_information is original
    assert getattr(original, name) == expected


@pytest.mark.parametrize("report_type", ["Inicial", "Final"])
def test_energy_visibility_preserves_value_and_summary_type(page, report, report_type):
    report.report_type = report_type
    before = deepcopy(report)
    page.set_report(report, page.project_directory)
    assert page.energy_meter_field.isVisible() == (report_type == "Inicial")
    assert page.energy_meter_label.isVisible() == (report_type == "Inicial")
    for name in ("delivered_keys", "consumer_unit", "general_notes", "issue_location"):
        assert getattr(page, f"{name}_field").isVisible()
    assert page.summary_fields["report_type"].text() == report_type
    assert report == before
    report.report_type = "Inicial"
    page.set_report(report, page.project_directory)
    assert page.energy_meter_field.text() == "123"


def test_summary_main_data_and_counts(page, report):
    report.sections = [Section("Sala", photos=[Photo("a.png"), Photo("b.png")]),
                       Section("Cozinha", photos=[Photo("c.png")])]
    page.set_report(report, page.project_directory)
    for key, value in {
        "title": "Vistoria da casa", "property": "Casa", "address": "Rua A, 10",
        "landlord": "Bruno", "tenant": "Carla", "sections": "2", "photos": "3",
    }.items():
        assert page.summary_fields[key].text() == value


def test_warnings_cover_only_requested_conditions(page, report):
    assert "Nenhum ambiente cadastrado" in page.warnings_label.text()
    assert "Nenhuma foto no relatório" in page.warnings_label.text()
    report.sections = [Section("Sala"), Section("Cozinha", description="Completa",
                                                photos=[Photo("a.png")])]
    page.set_report(report, page.project_directory)
    text = page.warnings_label.text()
    assert "Sala: ambiente sem descrição" in text
    assert "Sala: ambiente sem fotos" in text
    assert "Cozinha" not in text
    assert "Nenhum ambiente" not in text
    assert "Nenhuma foto" not in text


@pytest.mark.parametrize("has_section", [False, True])
def test_valid_fields_and_warnings_allow_generation(page, report, dialogs, tmp_path, has_section):
    if has_section:
        report.sections.append(Section("Sala"))
        page.set_report(report, page.project_directory)
    before = deepcopy(report)
    page.generate_button.click()
    destination = page.project_directory / "relatorios" / "relatorio-vistoria.docx"
    assert dialogs["generate"] == [(report, page.project_directory, destination)]
    assert dialogs["generate"][0][0] is report
    assert not dialogs["save"]
    assert (page.project_directory / "relatorios").is_dir()
    assert str(page.project_directory / "relatorios") in dialogs["success"][0][2]
    assert len(dialogs["success"]) == 1
    assert not dialogs["warning"]
    assert report == before


@pytest.mark.parametrize("target, name, missing, label", [
    ("report", "title", "   ", "Título"),
    ("report", "inspection_date", None, "Data da vistoria"),
    ("report", "inspector_name", "", "Responsável pela vistoria"),
    ("property", "property_type", "", "Tipo do imóvel"),
    ("property", "address", "", "Endereço"),
    ("landlord", "name", "", "Nome do locador"),
    ("tenant", "name", "", "Nome do locatário"),
])
def test_missing_required_field_blocks_without_mutation(
    page, report, dialogs, tmp_path, target, name, missing, label,
):
    setattr(report if target == "report" else getattr(report, target), name, missing)
    before = deepcopy(report)
    page.generate_button.click()
    assert not dialogs["generate"]
    assert not dialogs["save"]
    assert label in dialogs["warning"][0][2]
    assert report == before
    assert not list(tmp_path.rglob("*.docx"))


def test_missing_fields_message_lists_all_pending(page, dialogs):
    page.set_report(Report(), page.project_directory)
    page.generate_button.click()
    for label in ("Título", "Data da vistoria", "Responsável pela vistoria", "Tipo do imóvel",
                  "Endereço", "Nome do locador", "Nome do locatário"):
        assert label in dialogs["warning"][0][2]


def test_missing_directory_blocks_generation(page, report, dialogs):
    page.set_report(report)
    page.generate_button.click()
    assert not dialogs["save"]
    assert not dialogs["generate"]
    assert "pasta do projeto" in dialogs["warning"][0][2]


def test_generation_does_not_open_save_dialog(page, dialogs):
    page.generate_button.click()
    assert not dialogs["save"]
    assert dialogs["generate"]


@pytest.mark.parametrize("error", [OSError("disk error"), RuntimeError("template error")])
def test_generator_error_shows_friendly_message(page, report, dialogs, monkeypatch, error):
    before = deepcopy(report)

    def fail(*args):
        raise error

    monkeypatch.setattr(DocumentGenerator, "generate", fail)
    page.generate_button.click()
    assert len(dialogs["warning"]) == 1
    assert "Traceback" not in dialogs["warning"][0][2]
    assert str(error) not in dialogs["warning"][0][2]
    assert not dialogs["success"]
    assert report == before


def test_rebinding_does_not_mutate_previous_report(page, report):
    before = deepcopy(report)
    new = Report(report_type="Final")
    page.set_report(new)
    assert page.project_directory is None
    page.delivered_keys_field.setText("3")
    page.general_notes_field.setPlainText("Novas notas")
    assert new.complementary_information.delivered_keys == "3"
    assert new.complementary_information.general_notes == "Novas notas"
    assert report == before


def test_navigation_refreshes_summary_and_preserves_objects(qtbot, tmp_path):
    window = MainWindow(project_directory=tmp_path)
    qtbot.addWidget(window)
    window.continue_button.click()
    window.form_page.continue_button.click()
    window.parties_page.continue_button.click()
    window.environments_page.add_button.click()
    report = window.report
    section = report.sections[0]
    photo = Photo("image.png")
    section.add_photo(photo)
    complementary = report.complementary_information
    window.environments_page.continue_button.click()
    page = window.review_page
    assert page.report is report
    assert page.project_directory == window.project_directory
    page.delivered_keys_field.setText("2")
    page.back_button.click()
    assert window.pages.currentWidget() is window.environments_page
    report.title = "Atualizado"
    report.property.address = "Rua B"
    report.landlord.name = "Novo locador"
    window.environments_page.add_button.click()
    window.environments_page.continue_button.click()
    assert page.summary_fields["title"].text() == "Atualizado"
    assert page.summary_fields["address"].text() == "Rua B"
    assert page.summary_fields["landlord"].text() == "Novo locador"
    assert page.summary_fields["sections"].text() == "2"
    assert page.summary_fields["photos"].text() == "1"
    assert page.delivered_keys_field.text() == "2"
    assert report.sections[0] is section
    assert section.photos[0] is photo
    assert report.complementary_information is complementary


def test_report_directory_creation_error_is_friendly(page, dialogs):
    directory = page.project_directory
    directory.mkdir(parents=True)
    (directory / "relatorios").write_text("Cannot create directory here")
    page.generate_button.click()
    assert not dialogs["generate"]
    assert not dialogs["success"]
    assert len(dialogs["warning"]) == 1
    assert "Não foi possível gerar" in dialogs["warning"][0][2]
