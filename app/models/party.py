from dataclasses import dataclass


@dataclass
class Party:
    name: str = ""
    document: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
