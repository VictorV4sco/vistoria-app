from app.models.property import Property


def test_create_property_with_default_values() -> None:
    property = Property()

    assert property.property_type == ""
    assert property.description == ""
    assert property.address == ""
    assert property.number == ""
    assert property.complement == ""
    assert property.neighborhood == ""
    assert property.city == ""
    assert property.state == ""
    assert property.postal_code == ""
