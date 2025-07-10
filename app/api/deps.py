import jwt
from jwt import PyJWTError
from sqlalchemy.orm import Session

from app.models.website import Website
from app.db.session import SessionLocal
from fastapi import Security, HTTPException, status, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from app.models.user import User
from app.models.apikey import APIKey
from app.core.config import get_settings
from app.core.security import verify_key

settings = get_settings()

api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_from_api_key(
        api_key: str = Security(api_key_header_scheme),
        db: Session = Depends(get_db)
):
    """
    Dependency that authenticates a user based on a provided API key.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing"
        )

    # We use the prefix for a fast initial lookup
    prefix = api_key[:8]
    potential_key = db.query(APIKey).filter(APIKey.prefix == prefix).first()

    if not potential_key or not potential_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API key"
        )

    # Now perform the secure hash comparison
    if not verify_key(api_key, potential_key.hashed_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API key"
        )

    # Return the user object associated with the valid key
    return potential_key.user


class CookieAuthenticator:
    def __init__(self, name: str = "access_token"):
        self.cookie_name = name
        self.credentials_exception = HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Could not validate credentials",
            headers={"Location": "/login"}
        )

    async def __call__(
            self,
            request: Request,
            db: Session = Depends(get_db)
    ) -> User:

        token = request.cookies.get(self.cookie_name)

        if not token:
            raise self.credentials_exception


        try:
            payload = jwt.decode(token, settings.SECRET_KEY,
                                 algorithms=["HS256"])


            username: str = payload.get("sub")
            if username is None:
                raise self.credentials_exception


        except PyJWTError as e:
            raise self.credentials_exception

        user = db.query(User).filter(User.username == username).first()

        if user is None:
            raise self.credentials_exception


        return user


get_current_user = CookieAuthenticator()


def get_chatauth_from_api_key(
        api_key: str = Security(api_key_header_scheme),
        db: Session = Depends(get_db)
) -> tuple[User, Website]:
    """
    Dependency that authenticates a user AND identifies the associated website.
    """
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key is missing")

    prefix = api_key[:8]
    potential_key = db.query(APIKey).filter(APIKey.prefix == prefix).first()

    if not potential_key or not potential_key.is_active or not verify_key(api_key, potential_key.hashed_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or inactive API key")

    return (potential_key.user, potential_key.website)

async def redirect_if_authenticated(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    A dependency that checks for a valid authentication cookie.
    If found, it redirects the user to the dashboard.
    Used for public pages like /login and /signup.
    """
    token = request.cookies.get("access_token")

    # If there's no token, do nothing. The user can proceed.
    if not token:
        return

    try:
        # We still need to validate the token to make sure it's not fake or expired.
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            return # Invalid token, let them see the login page.
    except PyJWTError:
        return # Token is invalid/expired, let them see the login page.

    # Check if the user from the token still exists.
    user = db.query(User).filter(User.username == username).first()

    # If the user is valid, this is when we redirect.
    if user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Already authenticated",
            headers={"Location": "/dashboard"} # Redirect them to the dashboard
        )