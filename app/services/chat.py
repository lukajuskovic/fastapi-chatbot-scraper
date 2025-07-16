import io
from fastapi import HTTPException, Depends
from PIL import Image
import requests
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import google.generativeai as genai

from app.models.chat_session import Chat_session
from app.models.message import MessageSender
from .scraping import get_embedding
from app.core.config import get_settings
from app.crud.crud_chat_session import crud_chat_session
from app.crud.crud_message import crud_message
from app.crud.crud_scrapedcontent import crud_scraped_content
from app.schemas.chatbot import ChatRequest, ChatResponse
from app.schemas.message import MessageCreate
from app.api.deps import get_db
from ..schemas.chat_session import ChatSessionCreate


class ChatService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        settings = get_settings()
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.llm_model = genai.GenerativeModel("gemini-1.5-flash-latest")

    async def process_chat_request(self, chat_request: ChatRequest, auth_data: tuple) -> ChatResponse:
        """The main entrypoint for handling a user's chat message."""
        current_user, website = auth_data
        if not website:
            raise HTTPException(status_code=404, detail="Website not found.")

        # Find or create a chat session
        session = await self._find_or_create_session(website.id, chat_request.session_id)

        # Save the user's incoming message to the database
        await crud_message.create(self.db, obj_in=MessageCreate(
            chat_session_id=session.id, sender=MessageSender.USER, text=chat_request.query))

        # Get conversation history for the prompt
        history = await self._get_chat_history(session.id)
        # Find relevant context from scraped data using vector search
        context = await self._find_relevant_context(website.id, chat_request.query, history)
        # Generate a response from the LLM
        answer = self._generate_response(website.url, history, context, chat_request.query)

        # Save the bot's response to the database
        await crud_message.create(self.db, obj_in=MessageCreate(
            chat_session_id=session.id, sender=MessageSender.BOT, text=answer))

        # Return the response to the user
        return ChatResponse(answer=answer, session_id=str(session.id))

    async def _find_or_create_session(self, website_id: int, session_id: str | None) -> Chat_session:
        if session_id:
            session = await crud_chat_session.get(self.db, id=session_id)
            if session:
                return session

        session_data_in = ChatSessionCreate(website_id=website_id)
        res = await crud_chat_session.create(self.db, obj_in=session_data_in)
        return res


    async def _get_chat_history(self, session_id: uuid.UUID) -> str:
        """
        Retrieves the most recent messages from a chat session and formats them
        into a string for use in the prompt.
        """
        # Query the database for messages in the current session, ordered by time
        messages = await crud_message.get_messages_by_session(self.db,session_id = session_id)

        # Reverse the list to get chronological order and format into a "Sender: Text" string
        history = "\n".join([f"{msg.sender.value}: {msg.text}" for msg in reversed(messages)])
        return history


    def _generate_search_query(self, history: str, query: str) -> str:
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
            response = self.llm_model.generate_content(prompt)
            rewritten_query = response.text.strip().replace('"', '')
            return rewritten_query
        except Exception:
            # If the LLM call fails for any reason, fall back to the original query
            return query


    async def _find_relevant_context(self, website_id: int, query: str, history: str, top_k: int = 5) -> str:
        """
        Finds the most relevant text chunks from the database using vector similarity search.
        It first refines the user's query based on chat history for better results.
        """
        # 1. Use the LLM to generate a better, context-aware search query
        search_query = self._generate_search_query(history, query)

        # 2. Get the vector embedding for the refined query
        query_embedding = get_embedding(search_query)
        if not query_embedding:
            return ""

        # 3. Perform a vector similarity search (L2 distance) against the scraped content
        results= await crud_scraped_content.get_relevant_scraped_content(self.db, website_id = website_id,embedding = query_embedding,top_k = top_k)

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


    def _generate_response(self, website_url: str, history: str, context: str, query: str) -> str:
        """
        Builds the final prompt with context and history, then calls the LLM
        to generate the chatbot's answer.
        """


        # This detailed prompt sets the persona and rules for the LLM
        prompt_parts = [ f"""You are a friendly and helpful assistant for the website {website_url}. Your goal is to be both a knowledgeable expert about the site and a natural conversationalist.
    
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
        """
        ]

        # Handle the case where no relevant context was found in the database

        if not context:
            prompt_parts.append("No context was provided. The answer is not available in the website content.")
        else:
            for item in context:
                if item['type'] == 'text':
                    prompt_parts.append(f"Text from {item['source']}:\n{item['content']}\n---")
                elif item['type'] == 'image':
                    try:
                        # Fetch the image from its URL
                        response = requests.get(item['url'], stream=True, timeout=10)
                        response.raise_for_status()  # Raise an exception for bad status codes
                        # Open the image using Pillow
                        image = Image.open(io.BytesIO(response.content))

                        # Add the image and its description to the prompt
                        prompt_parts.append(f"Image from {item['source']} (Description: '{item['description']}'):")
                        prompt_parts.append(image)
                        prompt_parts.append("---\n")
                    except Exception as e:
                        print(f"Could not load image from {item['url']}: {e}")
                        prompt_parts.append(f"[Image at {item['url']} could not be loaded]")

        # Add the final parts of the prompt
        prompt_parts.append(f"\n--- CONVERSATION HISTORY ---\n{history}")
        prompt_parts.append(f"\n--- CURRENT QUESTION ---\nUser: {query}\n\nAssistant's Response:")

        try:
            # Send the complete prompt to the LLM and return its response text
            response = self.llm_model.generate_content(prompt_parts)
            return response.text
        except Exception as e:
            # Provide a fallback message if the API call fails
            return "I'm sorry, I'm having trouble connecting to my brain right now. Please try again later."

