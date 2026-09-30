"""Physical photo dimensions for the report's two-column layout."""

MAX_PHOTO_WIDTH_CM = 7.0
MAX_PHOTO_HEIGHT_CM = 6.5
PHOTO_DPI = 96


def fit_photo_dimensions(width_px: int, height_px: int) -> tuple[float, float]:
    """Fit positive pixel dimensions inside the photo box without upscaling.

    A deterministic 96 dpi defines the native size, independently of image
    metadata. Return width and height in centimetres, preserving pixel aspect.
    """
    width = width_px * 2.54 / PHOTO_DPI
    height = height_px * 2.54 / PHOTO_DPI
    scale = min(1.0, MAX_PHOTO_WIDTH_CM / width, MAX_PHOTO_HEIGHT_CM / height)
    return width * scale, height * scale
