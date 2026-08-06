from fastapi import HTTPException, UploadFile

from app.repositories.qr_repository import QRRepository

QR_IMAGE_URL = "/users/qr-image"


class QRService:
    def __init__(self, repo: QRRepository) -> None:
        self.repo = repo

    async def upload_qr(self, user_id, file: UploadFile):
        allowed_types = ["image/jpeg", "image/png"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG are allowed.")

        contents = await file.read()
        if len(contents) > 1 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 1MB.")

        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        try:
            user.qr_code = QR_IMAGE_URL
            user.qr_code_data = contents
            user.qr_code_content_type = file.content_type
            self.repo.save(user)
            return {
                "success": True,
                "message": "QR code uploaded successfully",
                "qr_code_url": QR_IMAGE_URL,
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to upload QR code: {str(exc)}")

    async def get_qr(self, user_id):
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.qr_code_data:
            raise HTTPException(status_code=404, detail="No QR code found for this user")
        return {"qr_code_url": QR_IMAGE_URL}

    async def get_qr_image(self, user_id):
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.qr_code_data or not user.qr_code_content_type:
            raise HTTPException(status_code=404, detail="No QR code found for this user")
        return user.qr_code_data, user.qr_code_content_type

    async def delete_qr(self, user_id):
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.qr_code_data:
            raise HTTPException(status_code=404, detail="No QR code found for this user")

        try:
            user.qr_code = None
            user.qr_code_data = None
            user.qr_code_content_type = None
            self.repo.save(user)
            return {"success": True, "message": "QR code deleted successfully"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to delete QR code: {str(exc)}")
