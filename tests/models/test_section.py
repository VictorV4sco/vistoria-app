from app.models.section import Section


def test_create_section_with_default_values() -> None:
    section = Section(name="Sala")

    assert section.id is not None
    assert section.name == "Sala"
    assert section.description == ""
    assert section.notes == ""
    assert section.order == 0
    assert section.photos == []
