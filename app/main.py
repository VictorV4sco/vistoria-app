"""Application entry point."""

from app import __version__


def main() -> None:
    """Start the application.

    The graphical interface will be introduced in a later epic.
    """
    print(f"VistoriaApp {__version__}")


if __name__ == "__main__":
    main()
