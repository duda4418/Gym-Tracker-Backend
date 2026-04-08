from sqlalchemy.orm import Session

from app.db.models.users import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_auth_id(self, auth_id: str) -> User | None:
        return self.session.query(User).filter_by(auth_id=str(auth_id)).first()

    def get_by_id(self, user_id) -> User | None:
        return self.session.query(User).filter_by(id=user_id).first()

    def get_id_by_auth_id(self, auth_id: str):
        return self.session.query(User.id).filter_by(auth_id=str(auth_id)).scalar()

    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
