from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chatbot import ChatRequest, ChatResponse
from app.api.deps import get_db, get_chatauth_from_api_key

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.chat import ChatService

chatbot_router = APIRouter(prefix="/chat")
templates = Jinja2Templates(directory="templates")


@chatbot_router.get("/", response_class=HTMLResponse)
async def dash(
    request: Request,
):
    return templates.TemplateResponse(
        "chatbot.html",
        {"request": request}
    )
@chatbot_router.post("/", response_model=ChatResponse)
async def chat_with_website(
        chat_request: ChatRequest,
        auth_data: tuple = Depends(get_chatauth_from_api_key),
        chat_service: ChatService = Depends()
):
    return await chat_service.process_chat_request(
        chat_request=chat_request,
        auth_data=auth_data
    )