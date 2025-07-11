from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chatbot import ChatRequest, ChatResponse
from app.api.deps import get_db, get_chatauth_from_api_key

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.logic import chatting

chatbot_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@chatbot_router.get("/chat", response_class=HTMLResponse)
async def dash(
    request: Request,
):
    return templates.TemplateResponse(
        "chatbot.html",
        {"request": request}
    )
@chatbot_router.post("/chat", response_model=ChatResponse)
async def chat_with_website(
        chat_request: ChatRequest,
        db: AsyncSession = Depends(get_db),
        auth_data: tuple = Depends(get_chatauth_from_api_key)
):
    res = await chatting(chat_request,db,auth_data)
    return res