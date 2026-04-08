from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models.users import User


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_auth_id(self, auth_id: str):
        return self.session.query(User).filter_by(auth_id=str(auth_id)).first()

    def get_by_id(self, user_id):
        return self.session.query(User).filter_by(id=user_id).first()

    def get_by_email(self, email: str):
        return self.session.query(User).filter_by(email=email).first()

    def create_user(self, email: str, name: str, password_hash: str):
        user = User(id=uuid4(), auth_id=str(uuid4()), email=email, name=name, password_hash=password_hash)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def save_refresh_token(self, user: User, refresh_token_hash: str, refresh_token_expires_at):
        user.refresh_token_hash = refresh_token_hash
        user.refresh_token_expires_at = refresh_token_expires_at
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def clear_refresh_token(self, user: User):
        user.refresh_token_hash = None
        user.refresh_token_expires_at = None
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
