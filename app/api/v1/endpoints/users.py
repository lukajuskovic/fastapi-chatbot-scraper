import secrets
import uuid

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import multiprocessing

from app.crud import crud_user, crud_website
from app.models.user import User, APIKey
from app.models.chatbot import Website
from app.schemas.user import UserCreate, UserLogin
from app.schemas.api_key import APIKeyResponse, APIKeyInfo
from app.schemas.website import WebsiteCreate
from app.api.deps import get_db, get_current_user, redirect_if_authenticated
from app.services.scraping import scrape_site
from app.core.security import hash_key, hashing_password, verify_password, generate_jwt

# Initialize Jinja2 templates to render HTML pages
templates = Jinja2Templates(directory="templates")

# Create a new router for user-related endpoints
user_router = APIRouter()


# --- User Authentication Endpoints ---

@user_router.post("/signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Handles new user registration."""
    # Create a new User instance and hash the provided password
    user = User(username=user_data.username, email=user_data.email, hashed_password= hashing_password(user_data.password))

    # Add the new user to the database and save changes
    db.add(user)
    db.commit()

    return {"message": "User has been created"}


@user_router.get("/signup", response_class=HTMLResponse)
async def get_signup_page(request: Request, _=Depends(redirect_if_authenticated)):
    """Serves the HTML page for user registration."""
    return templates.TemplateResponse("signup.html", {"request": request})


@user_router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(
        response: Response,
        user_data: UserLogin,
        db: Session = Depends(get_db)
):
    """Handles user login and sets an access token cookie."""
    # Find the user by username and verify their password
    user = db.query(User).filter(User.username == user_data.username).first()
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
    return


@user_router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request, _=Depends(redirect_if_authenticated)):
    """Serves the HTML page for user login."""
    return templates.TemplateResponse("login.html", {"request": request})


@user_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    """Handles user logout by deleting the access token cookie."""
    response.delete_cookie(key="access_token", path="/")
    return


# --- API Key and Website Management Endpoints ---

@user_router.post("/api-keys", response_model=APIKeyResponse)
def create_api_key(
        website_data: WebsiteCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Creates a new Website record and an associated API key.
    Starts the scraping process in a separate background process.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="You must be logged in")

    # Check if the website already exists. If not, create it.
    existing_website = db.query(Website).filter(Website.url == website_data.url).first()
    if existing_website is None:
        new_website = Website(
            url=website_data.url,
            owner_id=current_user.id
        )
        db.add(new_website)
        db.commit()
        db.refresh(new_website)

        # Start the scraping function in a completely separate process
        # This prevents it from blocking the web server.
        scraper_process = multiprocessing.Process(
            target=scrape_site,
            args=(new_website.url, new_website.id)
        )
        scraper_process.start()

        web_id = new_website.id
    else:
        web_id = existing_website.id

    # Generate a new secure API key and its prefix
    new_key = f"{secrets.token_urlsafe(32)}"
    prefix = new_key[:8]
    hashed_key = hash_key(new_key)

    # Ensure the generated key prefix is unique
    if db.query(APIKey).filter(APIKey.prefix == prefix).first():
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not generate a unique API key, please try again.")

    # Create the new APIKey record in the database
    db_api_key = APIKey(
        hashed_key=hashed_key,
        prefix=prefix,
        user_id=current_user.id,
        website_id=web_id
    )
    db.add(db_api_key)
    db.commit()

    # Return the unhashed key to the user one time
    return APIKeyResponse(
        key=new_key,
        message="API key generated successfully. Please store it securely."
    )


@user_router.get("/api-keys", response_model=list[APIKeyInfo])
def get_user_api_keys(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Fetches all API keys belonging to the current user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user.api_keys


@user_router.delete("/api-keys/{key_id}", status_code=204)
def delete_api_key(key_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    key_to_delete = crud_user.get_api_key(db, key_id=key_id, user_id=current_user.id)

    if not key_to_delete:
        raise HTTPException(status_code=404, detail="API key not found")

    website = key_to_delete.website
    if len(website.api_keys) == 1:
        crud_website.delete_website(db, website=website)
    else:
        crud_user.delete_api_key(db, api_key=key_to_delete)

    db.commit()
    return Response(status_code=204)


# --- Dashboard and SSE Endpoints ---

@user_router.get("/dashboard", response_class=HTMLResponse)
async def dash(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    """Serves the main user dashboard HTML page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": current_user}
    )