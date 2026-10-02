import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.models.party import Party
from app.services.app_paths import AppPaths


@pytest.fixture
def service(tmp_path):
    from app.services.landlord_service import LandlordService

    return LandlordService(AppPaths(tmp_path / "app"))


def test_missing_agenda_is_empty_without_creating_files(service, tmp_path):
    assert service.list_landlords() == []
    assert list(tmp_path.iterdir()) == []


def test_round_trip_utf8_and_only_landlord_fields(service):
    landlord = Party("João da Conceição", "123.456.789-00", "21 9999", "a@b.com", "Rua São José")
    before = deepcopy(landlord)
    service.save(landlord)
    assert service.list_landlords() == [landlord]
    assert service.list_landlords()[0] is not landlord
    assert landlord == before
    text = service.app_paths.landlords_file.read_text(encoding="utf-8")
    assert "João" in text
    assert json.loads(text) == {"version": 1, "landlords": [vars(landlord)]}


def test_same_document_updates_without_duplicates(service):
    service.save(Party("Ana", "123.456.789-00", address="Rua A"))
    service.save(Party("Ana atualizada", "12345678900", address="Rua B"))
    assert service.list_landlords() == [Party("Ana atualizada", "12345678900", address="Rua B")]


def test_name_fallback_without_document_and_distinct_documents(service):
    service.save(Party(" Ana Maria "))
    service.save(Party("ana  maria", phone="Novo"))
    service.save(Party("ana maria", document="123"))
    service.save(Party("ana maria", document="456"))
    assert len(service.list_landlords()) == 3
    assert service.list_landlords()[0].phone == "Novo"


def test_empty_landlord_is_rejected_without_writing(service):
    with pytest.raises(ValueError):
        service.save(Party(name="  ", document=" "))
    assert not service.app_paths.landlords_file.exists()


@pytest.mark.parametrize("landlord", [
    Party(phone="(21) 99999-9999"), Party(email="ana@example.com"),
    Party(name="  ", document=" ", phone="111"),
    Party(document="---", email="ana@example.com"),
])
@pytest.mark.parametrize("existing", [False, True])
def test_contact_without_identity_cannot_create_or_change_agenda(service, landlord, existing):
    if existing:
        service.save(Party("Ana", "123"))
    path = service.app_paths.landlords_file
    before = path.read_bytes() if existing else None
    with pytest.raises(ValueError, match="Informe pelo menos o nome ou CPF/CNPJ"):
        service.save(landlord)
    if existing:
        assert path.read_bytes() == before
    else:
        assert not path.exists()
        assert not service.app_paths.app_root.exists()


def test_name_only_and_document_only_keep_independent_deduplication(service):
    service.save(Party(name=" Ana Maria "))
    service.save(Party(document="123.456.789-00"))
    assert len(service.list_landlords()) == 2
    service.save(Party(name="ana  maria", phone="111"))
    service.save(Party(document="12345678900", email="a@example.com"))
    assert service.list_landlords() == [
        Party(name="ana  maria", phone="111"),
        Party(document="12345678900", email="a@example.com"),
    ]


def test_delete_and_missing_delete_are_safe(service):
    first, second = Party("Ana", "123"), Party("Bruno", "456")
    service.save(first)
    service.save(second)
    service.delete(Party(document="123"))
    assert service.list_landlords() == [second]
    before = service.app_paths.landlords_file.read_bytes()
    service.delete(first)
    assert service.app_paths.landlords_file.read_bytes() == before


def test_delete_from_absent_agenda_does_not_create_file(service):
    service.delete(Party("Ausente"))
    assert not service.app_paths.landlords_file.exists()


def test_write_is_atomic_and_temporary_is_valid(service, monkeypatch):
    service.save(Party("Primeiro"))
    old = service.app_paths.landlords_file.read_bytes()
    replace = Path.replace
    calls = []

    def inspect(source, destination):
        assert destination == service.app_paths.landlords_file
        assert source.parent == destination.parent
        assert destination.read_bytes() == old
        assert json.loads(source.read_text(encoding="utf-8"))["landlords"][1]["name"] == "Segundo"
        calls.append(source)
        return replace(source, destination)

    monkeypatch.setattr(Path, "replace", inspect)
    service.save(Party("Segundo"))
    assert len(calls) == 1
    assert not calls[0].exists()
    assert list(service.app_paths.app_root.iterdir()) == [service.app_paths.landlords_file]


@pytest.mark.parametrize("operation", ["save", "delete"])
def test_failed_replace_preserves_agenda_and_cleans_temporary(service, monkeypatch, operation):
    landlord = Party("Ana")
    service.save(landlord)
    before = service.app_paths.landlords_file.read_bytes()
    monkeypatch.setattr(Path, "replace", Mock(side_effect=PermissionError("private path")))
    with pytest.raises(OSError):
        getattr(service, operation)(Party("Bruno") if operation == "save" else landlord)
    assert service.app_paths.landlords_file.read_bytes() == before
    assert list(service.app_paths.app_root.iterdir()) == [service.app_paths.landlords_file]


@pytest.mark.parametrize("content", [
    b"broken", b"\xff", b"[]", b'{"version":2,"landlords":[]}',
    b'{"version":1,"landlords":[{"name":42}]}',
    b'{"version":1,"landlords":{}}',
])
def test_corrupt_agenda_never_overwritten(service, content):
    service.app_paths.app_root.mkdir()
    service.app_paths.landlords_file.write_bytes(content)
    for operation in (service.list_landlords, lambda: service.save(Party("Ana")),
                      lambda: service.delete(Party("Ana"))):
        with pytest.raises(ValueError):
            operation()
        assert service.app_paths.landlords_file.read_bytes() == content


def test_read_io_failure_is_propagated(service, monkeypatch):
    monkeypatch.setattr(Path, "read_text", Mock(side_effect=PermissionError("private path")))
    with pytest.raises(OSError):
        service.list_landlords()
