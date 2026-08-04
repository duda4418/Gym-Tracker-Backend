from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_split_service
from app.schemas.splits import SplitCreate, SplitResponse
from app.schemas.users import AuthenticatedUser
from app.services.split_service import SplitService

splits_router = APIRouter(tags=["Splits"], dependencies=[Depends(get_current_user)])

@splits_router.get("/splits", response_model=List[SplitResponse])
async def get_splits(
    current_user: AuthenticatedUser = Depends(get_current_user),
    split_service: SplitService = Depends(get_split_service),
):
    return await split_service.get_splits(current_user.id)

@splits_router.post("/splits", response_model=SplitResponse, status_code=201)
async def create_split(
    data: SplitCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    split_service: SplitService = Depends(get_split_service),
):
    return await split_service.create_split(current_user.id, data)


@splits_router.get("/splits/{split_id}", response_model=SplitResponse)
async def get_split(
    split_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    split_service: SplitService = Depends(get_split_service),
):
    return await split_service.get_split(current_user.id, split_id)


@splits_router.put("/splits/{split_id}", response_model=SplitResponse)
async def update_split(
    split_id: UUID,
    data: SplitCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    split_service: SplitService = Depends(get_split_service),
):
    return await split_service.update_split(current_user.id, split_id, data)


@splits_router.delete("/splits/{split_id}", status_code=204)
async def delete_split(
    split_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    split_service: SplitService = Depends(get_split_service),
):
    await split_service.delete_split(split_id, current_user.id)
    return None
