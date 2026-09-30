from copy import deepcopy

import pytest

from app.models.report import Report
from app.models.section import Section
from app.ui.environments_page import EnvironmentsPage


@pytest.fixture
def page(qtbot):
    page = EnvironmentsPage()
    qtbot.addWidget(page)
    page.set_report(Report())
    page.show()
    return page


def test_empty_state_and_add(page):
    report = page.report
    assert page.empty_label.isVisible()
    assert page.add_button.isEnabled()
    page.add_button.click()
    assert page.report is report
    assert len(report.sections) == 1
    assert isinstance(report.sections[0], Section)
    assert report.sections[0].name == "Novo ambiente"
    assert report.sections[0].order == 0
    assert page.editors[0].section is report.sections[0]
    assert not page.empty_label.isVisible()
    page.add_button.click()
    assert [s.order for s in report.sections] == [0, 1]


def test_load_existing_and_rebind_without_mutation(page):
    sections = [Section("Sala", description="Descrição", notes="Notas", order=20),
                Section("Cozinha", order=10)]
    report = Report(sections=sections.copy())
    snapshot = deepcopy(report)
    page.set_report(report)
    page.set_report(report)
    assert len(page.editors) == 2
    assert all(e.section is s for e, s in zip(page.editors, sections, strict=True))
    assert page.editors[0].name_field.text() == "Sala"
    assert page.editors[0].description_field.toPlainText() == "Descrição"
    assert page.editors[0].notes_field.toPlainText() == "Notas"
    new_report = Report(sections=[Section("Outro")])
    page.set_report(new_report)
    page.editors[0].name_field.setText("Editado")
    page.add_button.click()
    page.editors[0].down_button.click()
    page.editors[0].remove_button.click()
    assert report == snapshot
    assert page.report is new_report


@pytest.mark.parametrize("name", ["name", "description", "notes"])
def test_edit_updates_same_section(page, name):
    section = Section("Sala")
    page.set_report(Report(sections=[section]))
    field = getattr(page.editors[0], f"{name}_field")
    value = "Novo nome" if name == "name" else "Texto\nSegunda linha"
    if name == "name":
        field.setText(value)
    else:
        field.setPlainText(value)
    assert page.report.sections[0] is section
    assert getattr(section, name) == value


def test_remove_correct_section_preserves_others(page):
    sections = [Section("Sala", order=i) for i in range(3)]
    page.set_report(Report(sections=sections.copy()))
    snapshots = deepcopy(sections)
    page.editors[1].remove_button.click()
    assert page.report.sections[0] is sections[0]
    assert page.report.sections[1] is sections[2]
    assert sections == snapshots
    assert [e.section for e in page.editors] == [sections[0], sections[2]]
    page.editors[0].remove_button.click()
    page.editors[0].remove_button.click()
    assert page.report.sections == []
    assert page.empty_label.isVisible()


@pytest.mark.parametrize("button, expected", [
    ("up_button", [1, 0, 2]), ("down_button", [0, 2, 1]),
])
def test_move_updates_model_and_visual_order(page, button, expected):
    sections = [Section(str(i), order=i * 10) for i in range(3)]
    page.set_report(Report(sections=sections.copy()))
    getattr(page.editors[1], button).click()
    assert all(page.report.sections[j] is sections[i] for j, i in enumerate(expected))
    assert all(page.editors[j].section is sections[i] for j, i in enumerate(expected))
    assert [s.order for s in page.report.sections] == [0, 1, 2]
    assert not page.editors[0].up_button.isEnabled()
    assert not page.editors[-1].down_button.isEnabled()


def test_boundaries_do_not_move(page):
    sections = [Section("Sala", order=0), Section("Cozinha", order=1)]
    page.set_report(Report(sections=sections.copy()))
    assert not page.editors[0].up_button.isEnabled()
    assert not page.editors[-1].down_button.isEnabled()
    page.editors[0].up_button.click()
    page.editors[-1].down_button.click()
    assert page.report.sections == sections


def test_add_after_existing_orders_appends(page):
    sections = [Section("Sala", order=10), Section("Cozinha", order=20)]
    page.set_report(Report(sections=sections.copy()))
    page.add_button.click()
    assert page.report.sections[:2] == sections
    assert page.report.sections[-1].order == 21
