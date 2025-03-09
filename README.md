# Chat LLM Backend

A FastAPI-based backend for a chat application with LLM integration.

## Features

- Email and password-based authentication
- JWT token-based authorization
- Conversation management
- Message history with pagination
- LLM integration (currently using a dummy implementation)
- SQLite database with async support

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
# From the prompting_backend directory:
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

- `POST /api/register` - Register a new user
- `POST /api/token` - Login and get access token

### Conversations

- `GET /api/conversations` - Get all conversations
- `POST /api/conversations` - Create a new conversation
- `PUT /api/conversations/{conversation_id}/title` - Update conversation title

### Messages

- `GET /api/conversations/{conversation_id}/messages` - Get messages with pagination
- `POST /api/conversations/{conversation_id}/converse` - Send a message and get LLM response

## Security Notes

1. In production:

   - Replace the dummy SECRET_KEY in auth.py with a secure key
   - Configure CORS with specific origins
   - Use a production-grade database
   - Implement rate limiting
   - Add proper logging
   - Implement a proper LLM integration

2. The current implementation uses SQLite for simplicity. For production, consider using PostgreSQL or another production-grade database.

## Development

The project structure follows FastAPI best practices:

```
app/
├── api/
│   └── endpoints.py
├── database/
│   └── database.py
├── models/
│   └── models.py
├── schemas/
│   └── schemas.py
├── utils/
│   ├── auth.py
│   └── llm.py
└── main.py
```
