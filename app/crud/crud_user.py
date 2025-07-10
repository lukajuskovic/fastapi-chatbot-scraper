from sqlalchemy.orm import Session
from app.crud.base_crud import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hashing_password
from pydantic import BaseModel

class CRUDUser(CRUDBase[User,UserCreate,BaseModel]):
    def get_user_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def create(self, db: Session, user: UserCreate) -> User:
        hashed_pass = hashing_password(user.password)
        db_user = User(username=user.username, email=user.email, hashed_password=hashed_pass)
        db.add(db_user)
        db.commit()
        return db_user


crud_user = CRUDUser(User)