from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.schemas.chatbot import ChatRequest, ChatResponse
from app.api.deps import get_db, get_chatauth_from_api_key

from app.models.chatbot import MessageSender
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services import logic

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
def chat_with_website(
        chat_request: ChatRequest,
        db: Session = Depends(get_db),
        auth_data: tuple = Depends(get_chatauth_from_api_key)
):
    """Main endpoint for chatbot functionality."""
    current_user, website = auth_data

    if not website:
        raise HTTPException(status_code=404, detail="Website not found or you do not have permission.")

    # Find or create a chat session
    session = logic.find_or_create_session(db, website.id, chat_request.session_id)

    # Save the user's incoming message to the database
    logic.save_message(db, session.id, MessageSender.USER, chat_request.query)

    # Get conversation history for the prompt
    history = logic.get_chat_history(db, session.id)

    # Find relevant context from scraped data using vector search
    context = logic.find_relevant_context(db, website.id, chat_request.query, history)

    # Generate a response from the LLM
    answer = logic.generate_response(website.url, history, context, chat_request.query)

    # Save the bot's response to the database
    logic.save_message(db, session.id, MessageSender.BOT, answer)

    # Return the response to the user
    return ChatResponse(answer=answer, session_id=str(session.id))