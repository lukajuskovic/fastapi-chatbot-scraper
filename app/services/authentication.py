from app.core.security import generate_jwt, verify_password
from app.crud.crud_user import crud_user
from app.schemas.user import UserLogin
from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession



async def logging_in(response: Response,
        user_data: UserLogin,
        db: AsyncSession):
    """Handles user login and sets an access token cookie."""
    # Find the user by username and verify their password
    user = await crud_user.get_user_by_username(db, username=user_data.username)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate a JWT for the authenticated user
    token = generate_jwt(user_data.username)

    # Set the JWT as a secure, HTTP-only cookie in the user's browser
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="strict",
        path="/",
        secure=False  # Set to True in production with HTTPS
    )

