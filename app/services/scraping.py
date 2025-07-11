from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import os
import csv
import fitz  # PyMuPDF
import docx  # python-docx
import io
import requests

from app.crud.crud_scrapedcontent import crud_scraped_content
from app.crud.crud_website import crud_website
from app.db.session import AsyncSessionLocal
from app.models.scrapedcontent import ScrapedContent
from app.models.website import ScrapingStatus, Website
from app.schemas.scrapedcontent import ScrapedContentCreate
from app.schemas.website import WebsiteUpdate

from app.db.session import SyncSessionLocal

CSV_FILENAME = "scraped_data_log.csv"
CSV_HEADERS = ['website_id', 'source_url', 'text_content', 'embedding_preview']

MODEL_PATH = "./embedding_model/all-MiniLM-L6-v2"
MODEL_NAME = 'all-MiniLM-L6-v2'
if os.path.isdir(MODEL_PATH):
    embedding_model = SentenceTransformer(MODEL_PATH)
    print("Model loaded from local path.")
else:
    print(f"Downloading model '{MODEL_NAME}'...")
    embedding_model = SentenceTransformer(MODEL_NAME)
    print(f"Saving model to '{MODEL_PATH}'...")
    embedding_model.save(MODEL_PATH)






def get_embedding(text: str):
    """Generates a vector embedding for a given piece of text."""
    if not text or not isinstance(text, str):
        return None
    # The .tolist() converts the numpy array to a standard Python list
    return embedding_model.encode(text.strip()).tolist()

'''
async def add_chunk_to_db_and_csv(
        db: AsyncSession,
        chunks_to_add: list,
        website_id: int,
        source_url: str
):
    """
    Adds a list of text chunks to the database and logs them to a CSV.
    This is now a batch operation for efficiency.
    """
    if not chunks_to_add:
        return

    # Batch add to database
    for text_chunk in chunks_to_add:
        embedding = get_embedding(text_chunk)
        if embedding:
            await crud_scraped_content.create(db,obj_in= ScrapedContentCreate(website_id = website_id,source_url = source_url, text_content = text_chunk, embedding=embedding))

    # Batch write to CSV
    #file_exists = os.path.exists(CSV_FILENAME)
    #with open(CSV_FILENAME, 'a', newline='', encoding='utf-8') as csvfile:
    #    writer = csv.writer(csvfile)
    #    if not file_exists:
    #        writer.writerow(CSV_HEADERS)

    #    for text_chunk in chunks_to_add:
    #        embedding_preview = "omitted"
    #        writer.writerow([website_id, source_url, text_chunk, embedding_preview])
'''


def add_chunk_to_db_and_csv(
        db: Session,  # The 'db' object is now a synchronous SQLAlchemy Session
        chunks_to_add: list,
        website_id: int,
        source_url: str
):
    """
    Adds a list of text chunks to the database using direct, synchronous
    SQLAlchemy operations and logs them to a CSV.
    """
    if not chunks_to_add:
        return

    # --- Database Logic ---
    # This loop now performs synchronous operations
    for chunk in chunks_to_add:
        # This handles both text strings and image dictionaries
        text_content = chunk if isinstance(chunk, str) else chunk.get("text_content")

        if text_content:
            embedding = get_embedding(text_content)
            if embedding:
                # 1. Create an instance of the SQLAlchemy model directly
                new_content = ScrapedContent(
                    website_id=website_id,
                    source_url=source_url,
                    text_content=text_content,
                    embedding=embedding
                )
                # 2. Add the new object to the session.
                # The actual commit will happen later in the main scrape_site function.
                db.add(new_content)
    db.commit()

def process_page_content(page_html: str, source_url: str) -> list[str]:
    """
    Processes HTML using a refined and correctly-ordered list of strategies
    to handle multiple modern website layouts.
    """
    soup = BeautifulSoup(page_html, 'lxml')
    chunks = []

    # Use a more specific main content selector to avoid headers/footers
    main_content = soup.find('main') or soup.find('article') or soup.find('div', role='main') or soup.body
    if not main_content:
        return []

    page_title_el = main_content.find('h1')
    page_title = page_title_el.get_text(strip=True) if page_title_el else ""

    # --- STRATEGY 1: Find Specific, High-Quality Repeating Containers (for lists/grids) ---
    print(f"  > Trying Strategy 1: Specific Container Detection...")
    # This selector list is now more comprehensive
    candidate_selectors = [
        'div.quote', 'div.card', 'div.product-card', 'div.item',
        'article.post', 'article.blog-post', 'li.list-item'
    ]
    for selector in candidate_selectors:
        items = main_content.select(selector)
        if len(items) > 2: # Found a promising pattern
            print(f"  > Success! Detected {len(items)} items using selector '{selector}'.")
            for item in items:
                text = item.get_text(separator="\n", strip=True)
                if text and len(text.split()) > 5:
                    chunks.append(f"Page Title: {page_title}\n\n{text}")
            return chunks # Return immediately on success

    # --- STRATEGY 2: Section-Based Chunking ---
    print(f"  > Strategy 1 Failed. Trying Strategy 2: Section-based Chunking...")
    sections = main_content.find_all('section', recursive=False) # Find top-level sections
    if len(sections) > 1:
        for section in sections:
            # We look for sections that have a heading AND significant text content
            heading = section.find(['h2', 'h3'])
            text = section.get_text(separator="\n", strip=True)
            if heading and len(text.split()) > 20:
                chunks.append(f"Page Title: {page_title}\nSection: {heading.get_text(strip=True)}\n\n{text}")
        if chunks:
            print(f"  > Success! Found {len(chunks)} chunks using Section Strategy.")
            return chunks

    # --- STRATEGY 3: ID-Based Chunking ---
    print(f"  > Strategy 2 Failed. Trying Strategy 3: ID-based Chunking...")
    # Find all divs that have an ID attribute, as they often mark distinct sections
    divs_with_id = main_content.find_all('div', id=True, recursive=False)
    if len(divs_with_id) > 1:
        for div in divs_with_id:
            text = div.get_text(separator="\n", strip=True)
            if len(text.split()) > 30: # Ensure the section has enough content
                chunks.append(f"Page Title: {page_title}\nSection ID: #{div['id']}\n\n{text}")
        if chunks:
            print(f"  > Success! Found {len(chunks)} chunks using ID-based Strategy.")
            return chunks

    # --- STRATEGY 4: Catch-All Fallback ---
    print(f"  > Strategy 3 Failed. Trying Strategy 4: Full Content Fallback...")
    full_text = main_content.get_text(separator="\n", strip=True)
    if full_text and len(full_text.split()) > 30:
        print(f"  > Success! Found a single content chunk using Full Content Fallback.")
        # We can try to create smaller chunks from the full text as a final refinement
        sub_chunks = full_text.split('\n\n') # Split by double newlines
        for sub_chunk in sub_chunks:
            if len(sub_chunk.split()) > 20:
                 chunks.append(f"Page Title: {page_title}\n\n{sub_chunk.strip()}")
        if chunks:
             return chunks

    print("  > All strategies failed to find meaningful chunks.")
    return []

def scrape_site(url: str, website_id: int):
    ######################################
    # Change the limit of pages visited to your liking, it is set to low number for testing
    max_pages_to_visit = 10
    #######################################
    start_url = url
    base_domain = urlparse(start_url).netloc
    db = SyncSessionLocal()
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        return
    try:
        website.scraping_status = ScrapingStatus.SCRAPING
        db.commit()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
            )
            page = context.new_page()

            urls_to_visit_queue = [start_url]
            visited_urls = set()

            while urls_to_visit_queue and len(visited_urls) < max_pages_to_visit:
                current_url = urls_to_visit_queue.pop(0)
                if current_url in visited_urls:
                    continue

                print(f"\nVisiting: {current_url}")
                visited_urls.add(current_url)

                chunks = []
                new_links = []

                try:
                    with requests.get(current_url, stream=True, timeout=15, headers={'User-Agent': '...'}) as r:
                        content_type = r.headers.get('content-type', '').lower()

                        if 'application/pdf' in content_type:
                            chunks = handle_pdf(r.content, current_url)
                            # Link extraction from PDFs is not feasible here

                        elif 'word' in content_type:  # Catches .doc, .docx
                            chunks = handle_docx(r.content, current_url)
                            # Link extraction from Word docs is not feasible

                        elif 'text/html' in content_type:
                            # It's HTML, so now we use Playwright to render it
                            page.goto(current_url, timeout=30000, wait_until="networkidle")
                            page_html = page.content()
                            chunks = handle_html(page_html, current_url)

                            soup = BeautifulSoup(page_html, 'lxml')
                            image_chunks = []
                            # Find all images that have an 'alt' tag, as this is our descriptive text
                            for img_tag in soup.find_all('img', alt=True):
                                alt_text = img_tag['alt'].strip()
                                # Only process images with meaningful descriptions
                                if alt_text and len(alt_text) > 10:
                                    img_src = img_tag.get('src')
                                    if img_src:
                                        # Convert relative URLs (e.g., /img/photo.jpg) to absolute URLs
                                        absolute_img_url = urljoin(current_url, img_src)
                                        # Create a special chunk for the image
                                        image_chunk = {
                                            "text_content": alt_text,  # The alt text is the "content"
                                            "image_url": absolute_img_url
                                        }
                                        image_chunks.append(image_chunk)

                            print(f"  > Found {len(image_chunks)} relevant images.")
                            if image_chunks:
                                # You'll need a slightly modified add function, or update the existing one
                                add_chunk_to_db_and_csv(db, image_chunks, website_id, current_url)

                            # 4. Find new links to visit
                            soup = BeautifulSoup(page_html, 'lxml')
                            for link_el in soup.find_all("a", href=True):
                                href = link_el['href']
                                absolute_url = urljoin(current_url, href.strip())
                                parsed_url = urlparse(absolute_url)
                                normalized_url = parsed_url._replace(fragment="", query="").geturl()

                                if (urlparse(normalized_url).netloc == base_domain and
                                        normalized_url not in visited_urls and
                                        normalized_url not in urls_to_visit_queue):
                                    urls_to_visit_queue.append(normalized_url)

                    print(f"  > Generated {len(chunks)} semantic chunks.")
                    if chunks:
                        add_chunk_to_db_and_csv(db, chunks, website_id, current_url)

                    # Add new links to the queue
                    if new_links:
                        urls_to_visit_queue.extend(new_links)

                except PlaywrightTimeoutError:
                    print(f"  [!] Timeout visiting {current_url}")
                except Exception as e:
                    print(f"  [!] Error processing {current_url}: {e}")
                    db.rollback()  # Rollback on error for this page

                time.sleep(0.5)

            print("\n--- Scraping Finished ---")
            print(f"Total pages visited: {len(visited_urls)}")
            browser.close()
    finally:
        website = db.query(Website).filter(Website.id == website_id).first()
        if website:
            website.scraping_status = ScrapingStatus.COMPLETED
            db.commit()
        db.close()


def handle_pdf(response_content: bytes, source_url: str) -> list:
    """Extracts text from a PDF's byte content."""
    chunks = []
    try:
        # Open the PDF from the byte stream
        pdf_document = fitz.open(stream=response_content, filetype="pdf")
        print(f"  > Processing PDF with {len(pdf_document)} pages.")
        full_text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            full_text += page.get_text() + "\n"

        # You can add more advanced chunking here, but for now, we'll treat the whole doc as one chunk
        if full_text.strip():
            chunks.append(full_text.strip())
    except Exception as e:
        print(f"  [!] Failed to process PDF from {source_url}: {e}")
    return chunks


def handle_docx(response_content: bytes, source_url: str) -> list:
    """Extracts text from a DOCX file's byte content."""
    chunks = []
    try:
        # The python-docx library needs a file-like object, so we use io.BytesIO
        document = docx.Document(io.BytesIO(response_content))
        print(f"  > Processing DOCX document.")
        full_text = "\n".join([para.text for para in document.paragraphs if para.text])

        if full_text.strip():
            chunks.append(full_text.strip())
    except Exception as e:
        print(f"  [!] Failed to process DOCX from {source_url}: {e}")
    return chunks


def handle_html(page_html: str, source_url: str) -> list:
    """Your existing function to process HTML content."""
    # This is just your process_page_content function, renamed for clarity
    print(f"  > Processing HTML page...")
    return process_page_content(page_html, source_url)  # Your existing strategies go here