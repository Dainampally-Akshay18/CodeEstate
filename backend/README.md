# Tech Monopoly - Backend

Real-time multiplayer board game backend built with FastAPI.

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory
│   ├── config.py               # Environment config loader
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── health.py           # Health check endpoint
│   │
│   ├── services/               # Business logic (Phase 3+)
│   │   ├── __init__.py
│   │   ├── game_engine.py
│   │   └── bot_engine.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── game_state.py       # Core game state model
│   │   └── schemas.py          # Additional schemas
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── firebase.py         # Firebase integration
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # Utility functions
│
├── main.py                     # Entry point
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
└── README.md
```

## 🚀 Quick Start

### 1. Setup Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add Firebase credentials
```

### 4. Run Application

```bash
python main.py
```

The app will be available at `http://localhost:8000`

### 5. Check Health

```bash
curl http://localhost:8000/health
```

## 📚 API Documentation

Once running, access Swagger UI at:
- **Swagger**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_health.py
```

## 📊 Development Phases

- **Phase 1** ✅ Backend Foundation + Project Structure
- **Phase 2** ⏳ Game State Models + Core Data Structures
- **Phase 3** ⏳ Game Engine (movement, dice, turns)
- **Phase 4** ⏳ Property System + Rent Logic
- **Phase 5** ⏳ Room System + Player Join Logic
- **Phase 6** ⏳ Firebase Integration (read/write/update)
- **Phase 7** ⏳ Multiplayer Sync + Turn Locking
- **Phase 8** ⏳ Bot System
- **Phase 9** ⏳ Game End + Cleanup Logic
- **Phase 10** ⏳ Refactoring + Optimization

## 🔐 Environment Variables

See `.env.example` for required Firebase configuration:

```
TYPE=service_account
PROJECT_ID=your_project_id
PRIVATE_KEY_ID=your_key_id
PRIVATE_KEY=your_private_key
CLIENT_EMAIL=your_client_email
CLIENT_ID=your_client_id
AUTH_URI=https://accounts.google.com/o/oauth2/auth
TOKEN_URI=https://oauth2.googleapis.com/token
AUTH_PROVIDER_X509_CERT_URL=...
CLIENT_X509_CERT_URL=...
```

## 🤓 Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## 📝 Notes

- Keep all game logic in backend (never trust frontend)
- Firebase is the single source of truth
- Backend validates all player actions
- Follow the PRD strictly for requirements
