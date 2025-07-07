#!/usr/bin/env python3
"""
Create a test workspace with a realistic project structure for testing cli_workspace.py
"""

import os
from pathlib import Path


def create_test_workspace():
    """Create a comprehensive test workspace structure"""

    # Base directory
    base_dir = Path("test_workspaces") / "python_workspace"

    # Create directory structure
    directories = [
        "src",
        "src/components",
        "src/utils",
        "src/services",
        "tests",
        "tests/unit",
        "tests/integration",
        "config",
        "docs",
        "scripts",
        ".github/workflows",
    ]

    for dir_path in directories:
        (base_dir / dir_path).mkdir(parents=True, exist_ok=True)

    # Create files with content
    files = {
        # Root files
        "README.md": """# Test Project

This is a test project for demonstrating the Ollama workspace tools.

## Features
- User authentication
- Data processing
- API integration

## Setup
1. Install dependencies
2. Configure environment
3. Run tests
""",
        ".env.example": """DATABASE_URL=postgresql://localhost/testdb
API_KEY=your-api-key-here
DEBUG=true
""",
        "requirements.txt": """fastapi==0.104.1
pytest==7.4.3
requests==2.31.0
sqlalchemy==2.0.23
pydantic==2.5.0
""",
        # Source files
        "src/__init__.py": '"""Test project source code"""',
        "src/main.py": """#!/usr/bin/env python3
\"\"\"Main application entry point\"\"\"

from fastapi import FastAPI
from src.components.auth import router as auth_router
from src.components.data import router as data_router

app = FastAPI(title="Test API", version="1.0.0")

app.include_router(auth_router, prefix="/auth")
app.include_router(data_router, prefix="/data")

@app.get("/")
def read_root():
    return {"message": "Welcome to Test API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
""",
        "src/components/__init__.py": "",
        "src/components/auth.py": """\"\"\"Authentication module\"\"\"

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    # TODO: Implement real authentication
    if request.username == "admin" and request.password == "secret":
        return Token(access_token="fake-token", token_type="bearer")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/me")
async def get_current_user():
    # TODO: Implement token validation
    return {"username": "admin", "email": "admin@example.com"}
""",
        "src/components/data.py": """\"\"\"Data processing module\"\"\"

from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()

# Sample data storage
data_store: List[Dict[str, Any]] = []

@router.get("/items")
async def get_items():
    return {"items": data_store, "count": len(data_store)}

@router.post("/items")
async def create_item(item: Dict[str, Any]):
    data_store.append(item)
    return {"id": len(data_store), "item": item}

@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if 0 <= item_id < len(data_store):
        removed = data_store.pop(item_id)
        return {"deleted": removed}
    return {"error": "Item not found"}
""",
        "src/utils/__init__.py": "",
        "src/utils/validators.py": """\"\"\"Input validation utilities\"\"\"

import re
from typing import Optional

def validate_email(email: str) -> bool:
    \"\"\"Validate email format\"\"\"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> Optional[str]:
    \"\"\"Validate password strength\"\"\"
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return "Password must contain uppercase letter"
    if not any(c.isdigit() for c in password):
        return "Password must contain a number"
    return None
""",
        "src/utils/helpers.py": """\"\"\"General helper functions\"\"\"

from datetime import datetime
import hashlib

def get_timestamp() -> str:
    \"\"\"Get current timestamp\"\"\"
    return datetime.now().isoformat()

def hash_password(password: str) -> str:
    \"\"\"Hash password using SHA256\"\"\"
    return hashlib.sha256(password.encode()).hexdigest()

def format_response(data: Any, message: str = "Success") -> Dict:
    \"\"\"Format API response\"\"\"
    return {
        "data": data,
        "message": message,
        "timestamp": get_timestamp()
    }
""",
        "src/services/__init__.py": "",
        "src/services/database.py": """\"\"\"Database service\"\"\"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
        # Test files
        "tests/__init__.py": "",
        "tests/conftest.py": """\"\"\"Test configuration\"\"\"

import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    return TestClient(app)
""",
        "tests/unit/test_validators.py": """\"\"\"Test validators\"\"\"

import pytest
from src.utils.validators import validate_email, validate_password

def test_validate_email():
    assert validate_email("user@example.com") is True
    assert validate_email("invalid-email") is False
    assert validate_email("user@") is False

def test_validate_password():
    assert validate_password("Short1") is not None
    assert validate_password("longenoughbutnocaps1") is not None
    assert validate_password("LongEnoughButNoNumber") is not None
    assert validate_password("ValidPass123") is None
""",
        "tests/integration/test_api.py": """\"\"\"Test API endpoints\"\"\"

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Test API"}

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_login_success(client):
    response = client.post("/auth/login",
        json={"username": "admin", "password": "secret"})
    assert response.status_code == 200
    assert "access_token" in response.json()
""",
        # Config files
        "config/settings.py": """\"\"\"Application settings\"\"\"

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Test API"
    debug: bool = False
    database_url: str = "sqlite:///./test.db"
    secret_key: str = "super-secret-key"

    class Config:
        env_file = ".env"

settings = Settings()
""",
        # Documentation
        "docs/API.md": """# API Documentation

## Authentication

### POST /auth/login
Login with username and password.

Request:
```json
{
    "username": "string",
    "password": "string"
}
```

### GET /auth/me
Get current user information.

## Data Management

### GET /data/items
Get all items.

### POST /data/items
Create a new item.

### DELETE /data/items/{id}
Delete an item by ID.
""",
        "docs/CONTRIBUTING.md": """# Contributing Guidelines

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
""",
        # Scripts
        "scripts/setup.sh": """#!/bin/bash
# Setup development environment

echo "Setting up development environment..."

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Setup complete!"
""",
        "scripts/run_tests.sh": """#!/bin/bash
# Run all tests

echo "Running tests..."
pytest tests/ -v --cov=src
""",
        # GitHub workflows
        ".github/workflows/ci.yml": """name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest tests/
""",
        # Additional files to make it realistic
        ".gitignore": """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.env
.coverage
htmlcov/
.pytest_cache/
""",
        "TODO.md": """# TODO List

- [ ] Implement real authentication with JWT
- [ ] Add database migrations
- [ ] Create user management endpoints
- [ ] Add input validation middleware
- [ ] Implement rate limiting
- [ ] Add comprehensive logging
- [ ] Create Docker configuration
- [ ] Write integration tests for all endpoints
- [x] Setup basic project structure
- [x] Create initial API endpoints
""",
    }

    # Write all files
    for file_path, content in files.items():
        full_path = base_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

        # Make shell scripts executable
        if file_path.endswith(".sh"):
            os.chmod(full_path, 0o755)

    print(f"✅ Created test workspace in '{base_dir}' with {len(files)} files")
    print(f"📁 Directory structure includes: {', '.join(directories[:5])}...")


if __name__ == "__main__":
    create_test_workspace()
