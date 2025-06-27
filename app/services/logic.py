import io

from PIL import Image
from fastapi import requests
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid

# Import local modules and classes
from app.models.chatbot import Website, ScrapedContent, Chat_session, Message, MessageSender
from .scraping import get_embedding

# Import and configure the Google Generative AI client
import google.generativeai as genai
from app.core.config import get_settings
from ..crud import crud_chatbot

# Load application settings and configure the Gemini API key
settings = get_settings()
genai.configure(api_key=settings.GOOGLE_API_KEY)

# Initialize the specific Gemini model to be used for generating responses
llm_model = genai.GenerativeModel("gemini-1.5-flash-latest")


def find_or_create_session(db: Session, website_id: int, session_id: str | None) -> Chat_session:
    if session_id:
        session = crud_chatbot.get_session(db, session_id=session_id)
        if session:
            return session

    new_session = crud_chatbot.create_session(db, website_id=website_id)
    db.commit()
    db.refresh(new_session)
    return new_session


def get_chat_history(db: Session, session_id: uuid.UUID) -> str:
    """
    Retrieves the most recent messages from a chat session and formats them
    into a string for use in the prompt.
    """
    # Query the database for messages in the current session, ordered by time
    messages = db.query(Message).filter(Message.chat_session_id == session_id).order_by(
        Message.time_created.desc()).all()

    # Reverse the list to get chronological order and format into a "Sender: Text" string
    history = "\n".join([f"{msg.sender.value}: {msg.text}" for msg in reversed(messages)])
    return history


def generate_search_query(history: str, query: str) -> str:
    """
    Uses the LLM to rewrite the user's query into a self-contained search term,
    using the conversation history for context. This improves retrieval accuracy.
    """
    # If there's no history, the original query is sufficient
    if not history.strip():
        return query

    # Create a prompt instructing the LLM to generate a better search query
    prompt = f"""Based on the following conversation history and the user's final question, generate a single, self-contained search query that can be used to find relevant information in a database.

    CONVERSATION HISTORY:
    {history}

    FINAL QUESTION: "{query}"

    Re-written Search Query:"""

    try:
        # Generate the rewritten query and clean it up
        response = llm_model.generate_content(prompt)
        rewritten_query = response.text.strip().replace('"', '')
        return rewritten_query
    except Exception:
        # If the LLM call fails for any reason, fall back to the original query
        return query


def find_relevant_context(db: Session, website_id: int, query: str, history: str, top_k: int = 5) -> str:
    """
    Finds the most relevant text chunks from the database using vector similarity search.
    It first refines the user's query based on chat history for better results.
    """
    # 1. Use the LLM to generate a better, context-aware search query
    search_query = generate_search_query(history, query)

    # 2. Get the vector embedding for the refined query
    query_embedding = get_embedding(search_query)
    if not query_embedding:
        return ""

    # 3. Perform a vector similarity search (L2 distance) against the scraped content
    results = db.query(ScrapedContent).filter(
        ScrapedContent.website_id == website_id
    ).order_by(
        ScrapedContent.embedding.l2_distance(query_embedding)
    ).limit(top_k).all()

    structured_context = []
    for item in results:
        if item.image_url:
            # This is an image chunk
            structured_context.append({
                "type": "image",
                "source": item.source_url,
                "url": item.image_url,
                "description": item.text_content  # The alt text
            })
        else:
            # This is a text chunk
            structured_context.append({
                "type": "text",
                "source": item.source_url,
                "content": item.text_content
            })

    return structured_context


def generate_response(website_url: str, history: str, context: str, query: str) -> str:
    """
    Builds the final prompt with context and history, then calls the LLM
    to generate the chatbot's answer.
    """
    # Handle the case where no relevant context was found in the database
    prompt_context=""
    if not context:
        prompt_context = "No context was provided. The answer is not available in the website content."
    else:
        for item in context:
            if item['type'] == 'text':
                prompt_context+=f"Text from {item['source']}:\n{item['content']}\n---"
            elif item['type'] == 'image':
                try:
                    # Fetch the image from its URL
                    response = requests.get(item['url'], stream=True, timeout=10)
                    response.raise_for_status()  # Raise an exception for bad status codes
                    # Open the image using Pillow
                    image = Image.open(io.BytesIO(response.content))

                    # Add the image and its description to the prompt
                    prompt_context.append+=f"Image from {item['source']} (Description: '{item['description']}'): {image}"
                    prompt_context.append+="---\n"
                except Exception as e:
                    print(f"Could not load image from {item['url']}: {e}")
                    prompt_context.append+=f"[Image at {item['url']} could not be loaded]"

    # This detailed prompt sets the persona and rules for the LLM
    prompt = f"""You are a friendly and helpful assistant for the website {website_url}. Your goal is to be both a knowledgeable expert about the site and a natural conversationalist.

    Follow these two rules for your responses:

    1.  **If the user's question seems to be about the website or its content:**
        *   Answer the question using the "CONTEXT FROM THE WEBSITE".
        *   Answer like you are an employee of the website.
        *   You MUST NOT mention the context directly. Do not say things like "Based on the provided text..." or "According to the context..." or "Based on what I see". Simply answer the question directly as if you already know the information.
        *   If the answer is not in the context, politely state that you couldn't find that specific information on the website.

    2.  **If the user's question is a general greeting or small talk.:**
        *   You should answer it naturally and conversationally using your own general knowledge. You do not need to use the provided context for this.
        *   If they are asking questions with topics unrelated to the website, politely tell them that is not your expertise.

    --- CONTEXT FROM THE WEBSITE ---
    {prompt_context}

    --- CONVERSATION HISTORY ---
    {history}

    --- CURRENT QUESTION ---
    User: {query}

    Assistant's Response:"""

    try:
        # Send the complete prompt to the LLM and return its response text
        response = llm_model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Provide a fallback message if the API call fails
        return "I'm sorry, I'm having trouble connecting to my brain right now. Please try again later."


def save_message(db: Session, session_id: uuid.UUID, sender: MessageSender, text: str):
    """Saves a single chat message (from either user or bot) to the database."""
    message = Message(
        chat_session_id=session_id,
        sender=sender,
        text=text
    )
    db.add(message)
    db.commit()