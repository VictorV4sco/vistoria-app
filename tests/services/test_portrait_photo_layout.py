from io import BytesIO

import pytest
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm
from PIL import Image, ImageOps

from app.models.photo import Photo
from app.models.report import Report
from app.models.section import Section
from app.services.document_generator import DocumentGenerator


@pytest.mark.parametrize("size, orientation", [
    ((120, 60), 1), ((60, 120), 1), ((2400, 1200), 1), ((1200, 2400), 1),
    ((120, 60), 6),
])
def test_word_box_preserves_orientation_content_and_native_size(tmp_path, size, orientation):
    source = tmp_path / "photo.jpg"
    image = Image.new("RGB", size, "red")
    image.paste("blue", (0, 0, size[0] // 2, size[1]))
    exif = Image.Exif()
    exif[274] = orientation
    image.save(source, quality=95, exif=exif)
    original_bytes = source.read_bytes()
    with Image.open(source) as original:
        expected = ImageOps.exif_transpose(original)
        expected_size = expected.size
        expected_colors = [expected.getpixel((expected.width // 4, expected.height // 4)),
                           expected.getpixel((3 * expected.width // 4, 3 * expected.height // 4))]
    report = Report(sections=[Section("Sala", photos=[Photo("photo.jpg", caption="Vista")])])
    destination = tmp_path / "report.docx"
    DocumentGenerator.generate(report, tmp_path, destination)
    document = Document(destination)
    photo_shape = document.inline_shapes[-1]
    assert photo_shape.width <= Cm(6)
    assert photo_shape.height <= Cm(8)
    assert photo_shape.width / photo_shape.height == pytest.approx(
        expected_size[0] / expected_size[1], rel=1e-5
    )
    assert photo_shape.width <= Cm(expected_size[0] * 2.54 / 96)
    assert photo_shape.height <= Cm(expected_size[1] * 2.54 / 96)
    blip = photo_shape._inline.xpath(".//a:blip")[0]
    blob = document.part.related_parts[blip.get(qn("r:embed"))].blob
    with Image.open(BytesIO(blob)) as optimized:
        assert optimized.width / optimized.height == pytest.approx(
            expected_size[0] / expected_size[1]
        )
        colors = [optimized.getpixel((optimized.width // 4, optimized.height // 4)),
                  optimized.getpixel((3 * optimized.width // 4, 3 * optimized.height // 4))]
        for actual, expected_color in zip(colors, expected_colors, strict=True):
            assert actual == pytest.approx(expected_color, abs=5)
    assert source.read_bytes() == original_bytes
