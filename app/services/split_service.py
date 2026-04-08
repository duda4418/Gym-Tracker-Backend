from fastapi import HTTPException

from app.schemas.splits import SplitMuscleResponse, SplitMuscleResponse2, SplitResponse, SplitResponse2
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

    async def get_splits(self, user_id) -> list[SplitResponse]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        splits = self.split_repo.list_for_user(user.id)
        exercise_counts = self.split_repo.get_today_exercise_counts_by_muscle(user.id)

        result: list[SplitResponse] = []
        for split in splits:
            top_muscles = self.split_repo.get_top_muscles_for_split(split.id)
            description = " / ".join([muscle.name for muscle in top_muscles])

            split_muscles = self.split_repo.get_split_muscles_with_details(split.id)
            muscles_data = [
                SplitMuscleResponse(
                    id=muscle.id,
                    name=muscle.name,
                    pic=f"/uploads/muscles/{muscle.pic}" if muscle.pic else None,
                    nr_of_exercises=split_muscle.nr_of_exercises,
                    nr_of_exercises_done_today=exercise_counts.get(muscle.id, 0),
                )
                for split_muscle, muscle in split_muscles
            ]
            result.append(
                SplitResponse(
                    id=split.id,
                    name=split.name,
                    pic=split.pic,
                    description=description,
                    muscles=muscles_data,
                )
            )
        return result

    async def create_split(self, user_id, data) -> SplitResponse2:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        split = self.split_repo.create(user.id, data.name, data.pic)

        return_muscles: list[SplitMuscleResponse2] = []
        for muscle_data in data.muscles:
            muscle = self.muscle_repo.get_by_id(muscle_data.muscle_id)
            if not muscle:
                raise HTTPException(status_code=400, detail=f"Muscle with ID {muscle_data.muscle_id} not found")

            self.split_repo.add_split_muscle(split.id, muscle.id, muscle_data.nr_of_exercises)
            return_muscles.append(
                SplitMuscleResponse2(
                    id=muscle.id,
                    name=muscle.name,
                    pic=muscle.pic,
                    nr_of_exercises=muscle_data.nr_of_exercises,
                )
            )

        self.split_repo.commit()
        return SplitResponse2(
            id=split.id,
            name=split.name,
            pic=split.pic,
            description=" / ".join([muscle.name for muscle in return_muscles]),
            muscles=return_muscles,
        )

    async def delete_split(self, split_id, user_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        split = self.split_repo.get_for_user(split_id, user.id)
        if not split:
            raise HTTPException(status_code=404, detail="Split not found or unauthorized access")

        self.split_repo.delete_split(split)
        self.split_repo.commit()
        return {"message": "Split deleted successfully"}
