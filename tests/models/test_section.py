from app.models.photo import Photo
from app.models.section import Section


def test_create_section_with_default_values() -> None:
    section = Section(name="Sala")

    assert section.id is not None
    assert section.name == "Sala"
    assert section.description == ""
    assert section.notes == ""
    assert section.order == 0
    assert section.photos == []


def test_add_photo_keeps_photos_sorted_by_order() -> None:
    section = Section(name="Sala")
    other_section = Section(name="Cozinha")
    first = Photo(file_path="imagens/primeira.jpg", order=10)
    second = Photo(file_path="imagens/segunda.jpg", order=20)

    section.add_photo(second)
    section.add_photo(first)

    assert section.photos == [first, second]
    assert [photo.order for photo in section.photos] == [10, 20]
    assert other_section.photos == []


def test_remove_photo_preserves_remaining_photos() -> None:
    first = Photo(file_path="imagens/primeira.jpg", order=0)
    second = Photo(file_path="imagens/segunda.jpg", order=1)
    third = Photo(file_path="imagens/terceira.jpg", order=2)
    section = Section(name="Sala", photos=[first, second, third])

    section.remove_photo(second)

    assert section.photos == [first, third]
    assert [photo.order for photo in section.photos] == [0, 2]


def test_remove_only_photo_leaves_empty_list() -> None:
    photo = Photo(file_path="imagens/sala.jpg")
    section = Section(name="Sala", photos=[photo])

    section.remove_photo(photo)

    assert section.photos == []


def test_reorder_photos_uses_updated_order() -> None:
    first = Photo(file_path="imagens/primeira.jpg", order=0)
    second = Photo(file_path="imagens/segunda.jpg", order=1)
    third = Photo(file_path="imagens/terceira.jpg", order=2)
    section = Section(name="Sala", photos=[first, second, third])
    first.order = 20
    second.order = 30
    third.order = 10

    section.reorder_photos()

    assert section.photos == [third, first, second]
    assert [photo.order for photo in section.photos] == [10, 20, 30]


def test_reorder_photos_with_empty_list() -> None:
    section = Section(name="Sala")

    section.reorder_photos()

    assert section.photos == []


def test_move_photo_normalizes_order_and_preserves_objects():
    photos = [Photo(file_path=str(i), order=i * 10) for i in range(3)]
    section = Section("Sala", photos=photos.copy())
    section.move_photo(photos[1], -1)
    assert all(
        a is b for a, b in zip(section.photos, [photos[1], photos[0], photos[2]], strict=True)
    )
    assert [p.order for p in section.photos] == [0, 1, 2]
    section.move_photo(photos[1], -1)
    assert section.photos[0] is photos[1]
    section.move_photo(photos[1], 1)
    assert all(a is b for a, b in zip(section.photos, photos, strict=True))
    section.move_photo(photos[2], 1)
    assert section.photos[-1] is photos[2]
