from fastapi import APIRouter, Depends, File, Response, UploadFile

from app.api.dependencies import get_current_user, get_profile_service, get_qr_service
from app.schemas.users import AuthenticatedUser
from app.services.profile_service import ProfileService
from app.services.qr_service import QRService

qrcode_router = APIRouter(tags=["QR Codes"], dependencies=[Depends(get_current_user)])

@qrcode_router.post("/users/upload-qr")
async def upload_qrcode(
        file: UploadFile = File(...),
        current_user: AuthenticatedUser = Depends(get_current_user),
        qr_service: QRService = Depends(get_qr_service),
):
    return await qr_service.upload_qr(current_user.id, file)


@qrcode_router.get("/users/get-qr")
async def get_qrcode(
    current_user: AuthenticatedUser = Depends(get_current_user),
    qr_service: QRService = Depends(get_qr_service),
):
    return await qr_service.get_qr(current_user.id)


@qrcode_router.get("/users/qr-image")
async def get_qrcode_image(
    current_user: AuthenticatedUser = Depends(get_current_user),
    qr_service: QRService = Depends(get_qr_service),
):
    contents, content_type = await qr_service.get_qr_image(current_user.id)
    return Response(
        content=contents,
        media_type=content_type,
        headers={"Cache-Control": "private, no-store"},
    )


@qrcode_router.delete("/users/delete-qr")
async def delete_qrcode(
    current_user: AuthenticatedUser = Depends(get_current_user),
    qr_service: QRService = Depends(get_qr_service),
):
    return await qr_service.delete_qr(current_user.id)


@qrcode_router.post("/users/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    return await profile_service.upload_profile_picture(current_user.id, file)


@qrcode_router.get("/users/profile-picture")
async def get_profile_picture(
    current_user: AuthenticatedUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    contents, content_type = await profile_service.get_profile_picture(current_user.id)
    return Response(
        content=contents,
        media_type=content_type,
        headers={"Cache-Control": "private, no-store"},
    )


@qrcode_router.delete("/users/profile-picture")
async def delete_profile_picture(
    current_user: AuthenticatedUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    return await profile_service.delete_profile_picture(current_user.id)
