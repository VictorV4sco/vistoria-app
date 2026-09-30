"""Generate fictional Word review material; never use real inspection data.

From the repository root:
    python -m scripts.generate_demo_report
Or with the development Docker environment:
    docker compose run --rm test python -m scripts.generate_demo_report

Initial and final reports are placed under tmp/demo_report/ (ignored by Git).
Re-running replaces only demonstration images and documents. No template is modified.
"""

from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw

from app.models.complementary_information import ComplementaryInformation
from app.models.party import Party
from app.models.photo import Photo
from app.models.property import Property
from app.models.report import Report
from app.models.section import Section
from app.services.document_generator import DocumentGenerator

OUTPUT_DIRECTORY = Path(__file__).resolve().parents[1] / "tmp" / "demo_report"


def create_test_photo(project: Path, number: int, caption: str) -> Photo:
    """Draw a labelled geometric test image with an obvious aspect ratio."""
    extension = "jpg" if number % 2 else "png"
    sizes = [(2000, 1200), (1200, 1800), (1600, 1600)]
    width, height = sizes[(number - 1) % len(sizes)]
    relative = Path("imagens/originals") / f"demo-{number:02d}.{extension}"
    destination = project / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.new("RGB", (width, height), (215, 225 - number * 10, 235)) as image:
        draw = ImageDraw.Draw(image)
        draw.rectangle((30, 30, width - 30, height - 30), outline="navy", width=12)
        radius = min(width, height) // 5
        x, y = width // 2, height // 2
        draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                     fill="orange", outline="navy", width=10)
        draw.line((60, height - 100, width - 60, height - 100), fill="navy", width=8)
        draw.text((70, 70), f"DEMO {number:02d} - IMAGEM FICTICIA", fill="navy", font_size=44)
        draw.text((70, 135), f"{width} x {height} - {extension.upper()}",
                  fill="navy", font_size=36)
        draw.text((70, height - 80), "TESTE VISUAL - SEM DADOS REAIS", fill="navy", font_size=30)
        image.save(destination)
    return Photo(file_path=relative.as_posix(), caption=caption, order=10 - number)


def build_demo_report(project: Path) -> Report:
    """Build four fictional rooms with 1, 2, 3 and 0 photos, respectively."""
    return Report(
        title="DEMONSTRAÇÃO FICTÍCIA — Vistoria do imóvel Jardim das Ideias",
        report_type="Inicial",
        code="DEMO-FICTÍCIO-2026-001",
        inspection_date=date(2026, 9, 28),
        issue_date=date(2026, 9, 29),
        inspector_name="João Exemplo — responsável fictício",
        property=Property(
            property_type="Apartamento fictício",
            description="Imóvel inteiramente fictício para inspeção visual do relatório Word.",
            address="Rua Imaginária das Acácias", number="123",
            complement="Bloco Exemplo — apartamento 42", neighborhood="Jardim Inventado",
            city="Cidade Fictícia", state="RJ", postal_code="00000-000 (fictício)",
        ),
        landlord=Party(
            name="José Locador Exemplo (fictício)", document="000.000.000-00 (inválido/teste)",
            phone="(00) 00000-0001 (fictício)", email="locador@example.invalid",
            address="Rua Imaginária Alfa, 10 — Cidade Fictícia/RJ",
        ),
        tenant=Party(
            name="Lúcia Locatária Exemplo (fictícia)",
            document="00.000.000/0000-00 (inválido/teste)",
            phone="(00) 00000-0002 (fictício)", email="locataria@example.invalid",
            address="Avenida Inventada Beta, 20 — Cidade Fictícia/RJ",
        ),
        complementary_information=ComplementaryInformation(
            delivered_keys="3 chaves fictícias — entrada, portão e caixa de correspondência",
            energy_meter="MEDIDOR-DEMO-001 — leitura fictícia de 123 kWh",
            consumer_unit="UNIDADE-FICTÍCIA-042",
            general_notes="Material de demonstração, sem validade como vistoria real. "
                          "Imagens geométricas geradas localmente; verificar acentos, proporções "
                          "e legendas com símbolos: & < >.",
            issue_location="Cidade Fictícia/RJ",
        ),
        sections=[
            Section(
                name="Sala de estar — demonstração", order=40,
                description="Paredes claras, piso cerâmico e janela ampla. "
                            "Descrição fictícia para conferir a leitura do documento.",
                notes="Observação fictícia: pequena marca próxima à porta de entrada.",
                photos=[create_test_photo(project, 1, "Vista geral fictícia — sala & janela")],
            ),
            Section(
                name="Cozinha — demonstração", order=10,
                description="Bancada, pia e revestimentos descritos apenas para teste visual.",
                photos=[create_test_photo(project, 2, "Bancada fictícia — orientação vertical"),
                        create_test_photo(project, 3, "")],
            ),
            Section(
                name="Quarto — hóspedes", order=30,
                description="Ambiente fictício com três imagens para verificar "
                            "a última linha ímpar.",
                notes="Conferir se a terceira imagem mantém a mesma largura das anteriores.",
                photos=[create_test_photo(project, 4, "Parede fictícia — visão frontal"),
                        create_test_photo(project, 5, "Janela fictícia — detalhe <teste>"),
                        create_test_photo(project, 6, "Porta fictícia — maçaneta e dobradiças")],
            ),
            Section(
                name="Área de serviço — sem fotos", order=20,
                description="Ambiente fictício sem registro fotográfico para conferir a omissão "
                            "do título correspondente.",
                notes="Observação de teste: ventilação e iluminação descritas sem imagens.",
            ),
        ],
    )


def main() -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    project = OUTPUT_DIRECTORY / "project"
    report = build_demo_report(project)
    destination = OUTPUT_DIRECTORY / "relatorio_demonstracao.docx"
    DocumentGenerator.generate(report, project, destination)
    print(f"DOCX: {destination}")
    report.report_type = "Final"
    final_destination = OUTPUT_DIRECTORY / "relatorio_demonstracao_final.docx"
    DocumentGenerator.generate(report, project, final_destination)
    print(f"DOCX: {final_destination}")
    photo_count = sum(len(section.photos) for section in report.sections)
    print(f"Ambientes: {len(report.sections)}; fotos: {photo_count}")
    print(f"Imagens originais e otimizadas: {project / 'imagens'}")


if __name__ == "__main__":
    main()
