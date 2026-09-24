from dataclasses import dataclass


@dataclass
class Property:
    property_type: str = ""
    description: str = ""
    address: str = ""
    number: str = ""
    complement: str = ""
    neighborhood: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
