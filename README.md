# ConciergeAI: Intelligent Chatbots for Your Website

ConciergeAI is a powerful, multi-tenant web service that allows business users to create intelligent, context-aware AI chatbots for their websites. The service works by scraping a provided website URL, processing and storing its content as vector embeddings, and deploying a chat interface that uses a Large Language Model (LLM) to answer questions based on the scraped data.

## Key Features

- **Automated Content Scraping**: Uses Playwright to navigate and extract meaningful text content and image descriptions from a target website.
- **Vector Embeddings**: Generates vector representations of the scraped text using Sentence-Transformers for powerful semantic search.
- **Secure Multi-Tenant System**: A complete user authentication system (signup, login, JWT cookies) ensures that users can only access and manage their own websites.
- **AI-Powered Chat**: Leverages Google's Gemini models to provide natural, context-aware answers based on the website's content and conversation history.
- **REST API for Chatbots**: Business users can generate unique API keys to interact with their website's chatbot programmatically.
- **Database Migrations**: Uses Alembic to manage and version the PostgreSQL database schema in a safe and reproducible way.
- **Modern Tech Stack**: Built with FastAPI, Pydantic, and SQLAlchemy for a high-performance, asynchronous-ready backend.

## Technology Stack

- **Backend**: FastAPI, Uvicorn
- **Database**: PostgreSQL
- **ORM & Migrations**: SQLAlchemy, Alembic
- **Vector Storage & Search**: pgvector
- **Authentication**: `passlib[bcrypt]`, PyJWT (for JWTs)
- **Configuration**: `pydantic-settings`, `.env` files
- **AI & Embeddings**: `google-generativeai`, `sentence-transformers`
- **Web Scraping**: `playwright`, `BeautifulSoup`
- **Frontend**: Jinja2 for templating, HTML, CSS, JavaScript

## Prerequisites

Before you begin, ensure you have the following installed on your system:
- **Python** (3.10 or newer)
- **PostgreSQL** (version 12 or newer)
- **Docker** (recommended for running PostgreSQL easily)
- An account with [Google AI Studio](https://aistudio.google.com/) to get a `GOOGLE_API_KEY`.

---

## Install Dependencies

File: requirements.txt

install all the packages using pip:

pip install -r requirements.txt
## Download the necessary browser binaries for Playwright

playwright install

## Set Up the PostgreSQL Database with Docker

This is the easiest way to get a PostgreSQL instance with the pgvector extension ready.

Run "docker compose up" in terminal.

The pgvector extension will be automatically installed you just need to activate it in your database.

## Configure Environment Variables

### --- Database Credentials ---
These should match the values from your PostgreSQL setup

DB_USER=myuser

DB_PASSWORD=mysecretpassword

DB_NAME=mydb

### --- JWT Secret ---
Generate a secure secret key using: openssl rand -hex 32

SECRET_KEY=a_very_long_and_random_secret_string_for_jwt

### --- Google Gemini API Key ---
Get this from Google AI Studio

GOOGLE_API_KEY=your_google_ai_api_key_here

## Database Migrations with Alembic

Alembic handles all database schema changes. After setting up your .env file, you need to apply the migrations to create all the necessary tables.

If you don't have an alembic directory, run: alembic init alembic
Then configure the alembic.ini and env.py files to connect to your database.

Apply All Migrations
Run the following command to create all tables in your empty database according to your models.py file.

alembic upgrade head

For Future Changes
Whenever you change your SQLAlchemy models (e.g., add a column), generate a new migration file:

alembic revision --autogenerate -m "Describe your change here"


## Running the Application

 Once your environment is set up and the database is migrated, you can start the FastAPI server.

uvicorn main:app --reload --host 0.0.0.0 --port 8000

## How to Use the Application

Homepage: Visit http://localhost:8000 to see the main landing page.

### Sign Up: Create a new business user account.

Next, you will be redirected to the login page.

After logging in you will see the dashboard.

### Dashboard:

Click "Add Website & Generate Key".

Enter the full URL of the website you want to scrape (e.g., https://example.com).

The system will add the website to the database, generate a unique API key, and start the scraping process in the background.

The new API key will be shown to you once. Copy it and store it securely.

### Chatbot Interface:

Navigate to the Chatbot page.

Paste your newly generated API key into the input field.

Start asking questions. The chatbot will use the scraped content to provide answers.
