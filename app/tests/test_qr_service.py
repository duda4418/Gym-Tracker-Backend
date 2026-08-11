import asyncio
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

from fastapi import UploadFile
from starlette.datastructures import Headers

from app.services.qr_service import QRService


class QRRepositoryStub:
    def __init__(self, user):
        self.user = user
        self.saved = False

    def get_user_by_id(self, _):
        return self.user

    def save(self, _):
        self.saved = True


def test_upload_qr_stores_image_in_user_record():
    user = SimpleNamespace(id=uuid4(), qr_code=None, qr_code_data=None, qr_code_content_type=None)
    repo = QRRepositoryStub(user)
    service = QRService(repo)
    upload = UploadFile(
        file=BytesIO(b"png-data"),
        filename="qr.png",
        headers=Headers({"content-type": "image/png"}),
    )

    result = asyncio.run(service.upload_qr(user.id, upload))

    assert user.qr_code_data == b"png-data"
    assert user.qr_code_content_type == "image/png"
    assert result["qr_code_url"] == "/users/qr-image"
    assert repo.saved is True


def test_get_qr_image_returns_stored_bytes_and_content_type():
    user = SimpleNamespace(
        id=uuid4(),
        qr_code=None,
        qr_code_data=b"png-data",
        qr_code_content_type="image/png",
    )
    service = QRService(QRRepositoryStub(user))

    assert asyncio.run(service.get_qr_image(user.id)) == (b"png-data", "image/png")


def test_upload_qr_accepts_webp():
    user = SimpleNamespace(id=uuid4(), qr_code=None, qr_code_data=None, qr_code_content_type=None)
    repo = QRRepositoryStub(user)
    service = QRService(repo)
    upload = UploadFile(
        file=BytesIO(b"webp-data"),
        filename="qr.webp",
        headers=Headers({"content-type": "image/webp"}),
    )

    asyncio.run(service.upload_qr(user.id, upload))

    assert user.qr_code_data == b"webp-data"
    assert user.qr_code_content_type == "image/webp"


def test_delete_qr_clears_stored_image():
    user = SimpleNamespace(
        id=uuid4(),
        qr_code="/uploads/qrcodes/legacy.png",
        qr_code_data=b"png-data",
        qr_code_content_type="image/png",
    )
    repo = QRRepositoryStub(user)
    service = QRService(repo)

    result = asyncio.run(service.delete_qr(user.id))

    assert result == {"success": True, "message": "QR code deleted successfully"}
    assert user.qr_code is None
    assert user.qr_code_data is None
    assert user.qr_code_content_type is None
    assert repo.saved is True