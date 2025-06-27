# app/crud/crud_website.py
import uuid
from sqlalchemy.orm import Session
from app.models.chatbot import Website, ScrapedContent, ScrapingStatus
from pgvector.sqlalchemy import Vector


def get_website_by_url(db: Session, url: str) -> Website | None:
    return db.query(Website).filter(Website.url == url).first()


def create_website(db: Session, url: str, owner_id: uuid.UUID) -> Website:
    db_website = Website(url=url, owner_id=owner_id)
    db.add(db_website)
    return db_website


def update_website_status(db: Session, website_id: int, status: ScrapingStatus):
    db_website = db.query(Website).filter(Website.id == website_id).first()
    if db_website:
        db_website.scraping_status = status
    # The commit will be handled by the scraping task


def create_scraped_content_chunks(db: Session, chunks: list, website_id: int, source_url: str):
    from app.services.scraping import get_embedding  # Avoid circular import

    for chunk in chunks:
        text_content = ""
        image_url = None
        if isinstance(chunk, str):
            text_content = chunk
        elif isinstance(chunk, dict):
            text_content = chunk.get("text_content")
            image_url = chunk.get("image_url")

        if text_content:
            embedding = get_embedding(text_content)
            if embedding:
                db_content = ScrapedContent(
                    website_id=website_id,
                    source_url=source_url,
                    text_content=text_content,
                    embedding=embedding,
                    image_url=image_url
                )
                db.add(db_content)


def get_relevant_scraped_content(db: Session, website_id: int, embedding: list[float], top_k: int) -> list[
    ScrapedContent]:
    return db.query(ScrapedContent).filter(
        ScrapedContent.website_id == website_id
    ).order_by(
        ScrapedContent.embedding.l2_distance(embedding)
    ).limit(top_k).all()


def delete_website(db: Session, website: Website):
    db.delete(website)