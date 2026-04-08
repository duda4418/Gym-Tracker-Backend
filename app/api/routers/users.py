from fastapi import APIRouter, Depends, UploadFile, File

from app.api.dependencies import get_current_user, get_qr_service
from app.schemas.users import AuthenticatedUser
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


@qrcode_router.delete("/users/delete-qr")
async def delete_qrcode(
    current_user: AuthenticatedUser = Depends(get_current_user),
    qr_service: QRService = Depends(get_qr_service),
):
    return await qr_service.delete_qr(current_user.id)
