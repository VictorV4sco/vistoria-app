from app.models.complementary_information import ComplementaryInformation


def test_create_complementary_information_with_default_values() -> None:
    information = ComplementaryInformation()

    assert information.delivered_keys == ""
    assert information.energy_meter == ""
    assert information.consumer_unit == ""
    assert information.general_notes == ""
    assert information.issue_location == ""
