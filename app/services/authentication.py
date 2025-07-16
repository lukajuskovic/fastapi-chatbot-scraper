from app.core.security import generate_jwt, verify_password
from app.crud.crud_user import crud_user
from app.schemas.user import UserLogin
from fastapi import HTTPException, Response, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db

class AuthenticationService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def login_user(self, response: Response, user_data: UserLogin):
        """
        Handles user login, verification, and setting the JWT cookie.
        """
        user = await crud_user.get_user_by_username(self.db, username=user_data.username)
        if not user or not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        token = generate_jwt(user_data.username)

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            samesite="strict",
            path="/",
            secure=False
        )