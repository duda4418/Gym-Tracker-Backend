import asyncio
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

from fastapi import UploadFile
from starlette.datastructures import Headers

from app.services.profile_service import PROFILE_PICTURE_URL, ProfileService


class UserRepositoryStub:
    def __init__(self, user):
        self.user = user
        self.saved = False

    def get_by_id(self, _):
        return self.user

    def update(self, user):
        self.saved = True
        return user


def test_upload_profile_picture_stores_image_in_user_record():
    user = SimpleNamespace(id=uuid4(), profile_pic_data=None, profile_pic_content_type=None)
    repo = UserRepositoryStub(user)
    service = ProfileService(repo)
    upload = UploadFile(
        file=BytesIO(b"webp-data"),
        filename="profile.webp",
        headers=Headers({"content-type": "image/webp"}),
    )

    result = asyncio.run(service.upload_profile_picture(user.id, upload))

    assert user.profile_pic_data == b"webp-data"
    assert user.profile_pic_content_type == "image/webp"
    assert result["profile_pic"] == PROFILE_PICTURE_URL
    assert repo.saved is True


def test_get_profile_picture_returns_stored_image():
    user = SimpleNamespace(
        id=uuid4(),
        profile_pic_data=b"image-data",
        profile_pic_content_type="image/png",
    )
    service = ProfileService(UserRepositoryStub(user))

    assert asyncio.run(service.get_profile_picture(user.id)) == (b"image-data", "image/png")


def test_delete_profile_picture_clears_stored_image():
    user = SimpleNamespace(
        id=uuid4(),
        profile_pic_data=b"image-data",
        profile_pic_content_type="image/png",
    )
    repo = UserRepositoryStub(user)
    service = ProfileService(repo)

    result = asyncio.run(service.delete_profile_picture(user.id))

    assert result == {"success": True, "message": "Profile picture deleted successfully"}
    assert user.profile_pic_data is None
    assert user.profile_pic_content_type is None
    assert repo.saved is True