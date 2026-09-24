from app.models.photo import Photo


def test_create_photo_with_default_values() -> None:
    photo = Photo(file_path="imagens/sala-01.jpg")

    assert photo.id is not None
    assert photo.file_path == "imagens/sala-01.jpg"
    assert photo.caption == ""
    assert photo.order == 0
