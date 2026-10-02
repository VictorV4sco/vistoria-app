"""A small local address book, independent of inspection projects."""

import json
import os
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.models.party import Party
from app.services.app_paths import AppPaths

LANDLORD_FIELDS = ("name", "document", "phone", "email", "address")


class MissingLandlordIdentityError(ValueError):
    """The reusable address book needs a nonempty deduplication key."""


class LandlordService:
    def __init__(self, app_paths: AppPaths) -> None:
        self.app_paths = app_paths

    @staticmethod
    def _key(landlord: Party) -> tuple[str, str]:
        document = "".join(char for char in landlord.document if char.isalnum()).casefold()
        if document:
            return "document", document
        return "name", " ".join(landlord.name.split()).casefold()

    def list_landlords(self) -> list[Party]:
        """Return independent copies; missing files are empty, corrupt files raise ValueError."""
        try:
            text = self.app_paths.landlords_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        data = json.loads(text)
        if (not isinstance(data, dict) or type(data.get("version")) is not int
                or data["version"] != 1 or not isinstance(data.get("landlords"), list)):
            raise ValueError("A agenda de locadores está inválida.")
        landlords = []
        for item in data["landlords"]:
            if (not isinstance(item, dict) or set(item) != set(LANDLORD_FIELDS)
                    or any(not isinstance(value, str) for value in item.values())):
                raise ValueError("A agenda de locadores está inválida.")
            landlords.append(Party(**item))
        return landlords

    def save(self, landlord: Party) -> None:
        key = self._key(landlord)
        if not key[1]:
            raise MissingLandlordIdentityError(
                "Informe pelo menos o nome ou CPF/CNPJ do locador para salvá-lo na agenda."
            )
        landlords = self.list_landlords()
        # Keep order and deterministically replace a matching record.
        index = next((i for i, saved in enumerate(landlords) if self._key(saved) == key), None)
        copied = Party(**asdict(landlord))
        if index is None:
            landlords.append(copied)
        else:
            landlords[index] = copied
        self._write(landlords)

    def delete(self, landlord: Party) -> None:
        landlords = self.list_landlords()
        remaining = [saved for saved in landlords if self._key(saved) != self._key(landlord)]
        if len(remaining) != len(landlords):
            self._write(remaining)

    def _write(self, landlords: list[Party]) -> None:
        destination = self.app_paths.landlords_file
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=destination.parent,
                prefix=".locadores-", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump({"version": 1, "landlords": [asdict(party) for party in landlords]},
                          stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(destination)
        finally:
            if temporary is not None:
                with suppress(OSError):
                    temporary.unlink(missing_ok=True)
