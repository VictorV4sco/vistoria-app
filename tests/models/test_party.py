from app.models.party import Party


def test_create_party_with_default_values() -> None:
    party = Party()

    assert party.name == ""
    assert party.document == ""
    assert party.phone == ""
    assert party.email == ""
    assert party.address == ""
