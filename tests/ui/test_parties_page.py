from copy import deepcopy

import pytest

from app.models.party import Party
from app.models.report import Report
from app.ui.parties_page import PartiesPage

FIELDS = ("name", "document", "phone", "email", "address")


@pytest.fixture
def report():
    return Report(
        landlord=Party("Ana", "123", "111", "ana@example.com", "Rua A"),
        tenant=Party("Bruno", "456", "222", "bruno@example.com", "Rua B"),
    )


@pytest.fixture
def page(qtbot, report):
    page = PartiesPage()
    qtbot.addWidget(page)
    page.set_report(report)
    page.show()
    return page


@pytest.mark.parametrize("role", ["landlord", "tenant"])
def test_loads_existing_party(page, report, role):
    for name in FIELDS:
        assert getattr(page, f"{role}_{name}_field").text() == getattr(getattr(report, role), name)


@pytest.mark.parametrize("role", ["landlord", "tenant"])
@pytest.mark.parametrize("name", FIELDS)
def test_edit_updates_original_party(page, report, role, name, qtbot):
    original = getattr(report, role)
    other_role = "tenant" if role == "landlord" else "landlord"
    other = deepcopy(getattr(report, other_role))
    field = getattr(page, f"{role}_{name}_field")
    field.clear()
    qtbot.keyClicks(field, "Novo valor")
    assert getattr(report, role) is original
    assert getattr(original, name) == "Novo valor"
    assert getattr(report, other_role) == other
    field.clear()
    assert getattr(original, name) == ""


def test_rebinding_does_not_change_previous_or_new_report(page, report):
    previous = deepcopy(report)
    new_report = Report(landlord=Party(name="Carla"), tenant=Party(name="Daniel"))
    expected_new = deepcopy(new_report)
    parties = (new_report.landlord, new_report.tenant)
    page.set_report(new_report)
    assert report == previous
    assert new_report == expected_new
    for role in ("landlord", "tenant"):
        for name in FIELDS:
            assert getattr(page, f"{role}_{name}_field").text() == getattr(
                getattr(new_report, role), name
            )
            getattr(page, f"{role}_{name}_field").setText("Editado")
            assert getattr(getattr(new_report, role), name) == "Editado"
    assert new_report.landlord is parties[0]
    assert new_report.tenant is parties[1]
    assert report == previous
