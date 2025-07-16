import uuid

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.crud.crud_user import crud_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.schemas.api_key import APIKeyResponse, APIKeyInfo
from app.schemas.website import WebsiteCreate, WebsiteURLRequest
from app.api.deps import get_db, get_current_user, redirect_if_authenticated
from app.services.authentication import AuthenticationService
from app.services.dashboard import DashboardService

# Initialize Jinja2 templates to render HTML pages
templates = Jinja2Templates(directory="templates")

# Create a new router for user-related endpoints
user_router = APIRouter()


# --- User Authentication Endpoints ---

@user_router.post("/signup")
async def signup(user_data: UserCreate,
           db: AsyncSession = Depends(get_db)):
    """Handles new user registration."""
    await crud_user.create(db, obj_in=user_data)
    return {"message": "User has been created"}


@user_router.get("/signup", response_class=HTMLResponse, dependencies= [Depends(redirect_if_authenticated)])
async def get_signup_page(request: Request):
    """Serves the HTML page for user registration."""
    return templates.TemplateResponse("signup.html", {"request": request})

@user_router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(
        response: Response,
        user_data: UserLogin,
        auth_service: AuthenticationService = Depends()
):
    await auth_service.login_user(response=response, user_data=user_data)


@user_router.get("/login", response_class=HTMLResponse, dependencies=[Depends(redirect_if_authenticated)])
async def get_login_page(request: Request):
    """Serves the HTML page for user login."""
    return templates.TemplateResponse("login.html", {"request": request})


@user_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    """Handles user logout by deleting the access token cookie."""
    response.delete_cookie(key="access_token", path="/")
    return


# --- API Key and Website Management Endpoints ---

@user_router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
        web_info: WebsiteURLRequest,
        current_user: User = Depends(get_current_user),
        dashboard_service: DashboardService = Depends()
):
    if not current_user:
        raise HTTPException(status_code=401, detail="You must be logged in")

    key = await dashboard_service.create_website_and_api_key(
        website_data=WebsiteCreate(url=web_info.url,owner_id=current_user.id)
    )
    return {
        "key": key,
        "message": "API key generated successfully. Scraping has started."
    }


@user_router.get("/api-keys", response_model=list[APIKeyInfo])
async def get_user_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return current_user.api_keys


@user_router.delete("/api-keys/{key_id}", status_code=204)
async def delete_api_key(
        key_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        dashboard_service: DashboardService = Depends()
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await dashboard_service.delete_api_key(key_id=key_id, current_user=current_user)

    return Response(status_code=204)

# --- Dashboard and SSE Endpoints ---

@user_router.get("/dashboard", response_class=HTMLResponse)
async def dash(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse("dashboard.html",{"request": request, "user": current_user})