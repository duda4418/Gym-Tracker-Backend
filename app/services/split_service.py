from fastapi import HTTPException

from app.schemas.splits import SplitMuscleResponse, SplitResponse
from app.repositories.muscle_repository import MuscleRepository
from app.repositories.split_repository import SplitRepository
from app.repositories.user_repository import UserRepository


class SplitService:
    def __init__(
        self,
        split_repo: SplitRepository,
        user_repo: UserRepository,
        muscle_repo: MuscleRepository,
    ) -> None:
        self.split_repo = split_repo
        self.user_repo = user_repo
        self.muscle_repo = muscle_repo

    @staticmethod
    def _to_response(split) -> SplitResponse:
        return SplitResponse(
            id=split.id,
            name=split.name,
            pic=split.pic,
            muscles=[
                SplitMuscleResponse(
                    muscle_id=link.muscle_id,
                    nr_of_exercises=link.nr_of_exercises,
                )
                for link in split.muscles
            ],
        )

    def _require_user(self, user_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")
        return user

    def _require_split(self, split_id, user_id):
        split = self.split_repo.get_for_user(split_id, user_id)
        if not split:
            raise HTTPException(status_code=404, detail="Split not found")
        return split

    def _validate_muscles(self, muscles) -> None:
        muscle_ids = [item.muscle_id for item in muscles]
        if len(muscle_ids) != len(set(muscle_ids)):
            raise HTTPException(status_code=400, detail="A muscle can only appear once in a split")
        for muscle_id in muscle_ids:
            if not self.muscle_repo.get_by_id(muscle_id):
                raise HTTPException(status_code=404, detail=f"Muscle with ID {muscle_id} not found")

    async def get_splits(self, user_id) -> list[SplitResponse]:
        user = self._require_user(user_id)
        return [self._to_response(split) for split in self.split_repo.list_for_user(user.id)]

    async def get_split(self, user_id, split_id) -> SplitResponse:
        user = self._require_user(user_id)
        return self._to_response(self._require_split(split_id, user.id))

    async def create_split(self, user_id, data) -> SplitResponse:
        user = self._require_user(user_id)
        self._validate_muscles(data.muscles)

        split = self.split_repo.create(user.id, data.name, data.pic)
        for muscle_data in data.muscles:
            self.split_repo.add_split_muscle(
                split.id,
                muscle_data.muscle_id,
                muscle_data.nr_of_exercises,
            )

        self.split_repo.commit()
        return self._to_response(split)

    async def update_split(self, user_id, split_id, data) -> SplitResponse:
        user = self._require_user(user_id)
        split = self._require_split(split_id, user.id)
        self._validate_muscles(data.muscles)
        return self._to_response(self.split_repo.update(split, data.name, data.pic, data.muscles))

    async def delete_split(self, split_id, user_id):
        user = self._require_user(user_id)
        split = self._require_split(split_id, user.id)

        self.split_repo.delete_split(split)
        self.split_repo.commit()
        return {"message": "Split deleted successfully"}
