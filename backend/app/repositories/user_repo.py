"""User repository — all user-related database operations."""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, email: str, password: str, full_name: str, role: str = "analyst") -> User:
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()

    def update_active(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)
        return user

