from fastapi import HTTPException, UploadFile

from app.core.config import get_settings
from app.repositories.user_repository import UserRepository

PROFILE_PICTURE_URL = "/users/profile-picture"
settings = get_settings()


class ProfileService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def upload_profile_picture(self, user_id, file: UploadFile) -> dict:
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JPEG, PNG, and WebP are allowed.",
            )

        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.profile_pic_data = contents
        user.profile_pic_content_type = file.content_type
        self.repo.update(user)
        return {
            "success": True,
            "message": "Profile picture uploaded successfully",
            "profile_pic": settings.asset_url(PROFILE_PICTURE_URL),
        }

    async def get_profile_picture(self, user_id) -> tuple[bytes, str]:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.profile_pic_data or not user.profile_pic_content_type:
            raise HTTPException(status_code=404, detail="No profile picture found for this user")
        return user.profile_pic_data, user.profile_pic_content_type

    async def delete_profile_picture(self, user_id) -> dict:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.profile_pic_data:
            raise HTTPException(status_code=404, detail="No profile picture found for this user")

        user.profile_pic_data = None
        user.profile_pic_content_type = None
        self.repo.update(user)
        return {"success": True, "message": "Profile picture deleted successfully"}