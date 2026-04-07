import os

from fastapi import HTTPException, UploadFile

from app.core.config import get_settings
from app.repositories.qr_repository import QRRepository

BUCKET_NAME = "qrcodes"
settings = get_settings()


class QRService:
    def __init__(self, repo: QRRepository) -> None:
        self.repo = repo

    async def upload_qr(self, auth_id: str, file: UploadFile):
        allowed_types = ["image/jpeg", "image/png"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG are allowed.")

        contents = await file.read()
        if len(contents) > 1 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 1MB.")

        user = self.repo.get_user_by_auth_id(auth_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ".png"
        if not file_extension:
            file_extension = ".png"

        storage_dir = os.path.join(settings.UPLOADS_DIR, BUCKET_NAME, str(user.id))
        os.makedirs(storage_dir, exist_ok=True)
        storage_path = os.path.join(storage_dir, f"qrcode{file_extension}")

        try:
            with open(storage_path, "wb") as f:
                f.write(contents)

            public_url = f"/uploads/{BUCKET_NAME}/{user.id}/qrcode{file_extension}"
            user.qr_code = public_url
            self.repo.save(user)
            return {
                "success": True,
                "message": "QR code uploaded successfully",
                "qr_code_url": public_url,
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to upload QR code: {str(exc)}")

    async def get_qr(self, auth_id: str):
        user = self.repo.get_user_by_auth_id(auth_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.qr_code:
            raise HTTPException(status_code=404, detail="No QR code found for this user")
        return {"qr_code_url": user.qr_code}

    async def delete_qr(self, auth_id: str):
        user = self.repo.get_user_by_auth_id(auth_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.qr_code:
            raise HTTPException(status_code=404, detail="No QR code found for this user")

        try:
            relative_path = user.qr_code.replace("/uploads/", "")
            absolute_path = os.path.join(settings.UPLOADS_DIR, relative_path)
            if os.path.exists(absolute_path):
                os.remove(absolute_path)

            user.qr_code = None
            self.repo.save(user)
            return {"success": True, "message": "QR code deleted successfully"}
        except Exception as exc:
            user.qr_code = None
            self.repo.save(user)
            return {
                "success": False,
                "message": f"Failed to delete file, but database updated: {str(exc)}",
            }
