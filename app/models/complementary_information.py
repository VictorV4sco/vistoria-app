from dataclasses import dataclass


@dataclass
class ComplementaryInformation:
    delivered_keys: str = ""
    energy_meter: str = ""
    consumer_unit: str = ""
    general_notes: str = ""
    issue_location: str = ""
