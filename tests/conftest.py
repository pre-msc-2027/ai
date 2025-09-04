"""
Common test fixtures for SecuScan AI test suite
"""

import json
import os
import tempfile
from typing import Any, Dict, Generator, List
from unittest.mock import Mock, patch

import pytest

# Constants for test files
TEST_PYTHON_FILE = "test.py"
TEST_JS_FILE = "main.js"


@pytest.fixture
def mock_warnings() -> List[Dict[str, Any]]:
    """Sample warnings data for testing"""
    return [
        {"id": 0, "rule_id": 0, "file": TEST_PYTHON_FILE, "line": 10},
        {"id": 1, "rule_id": 1, "file": TEST_JS_FILE, "line": 25},
        {"id": 2, "rule_id": 0, "file": TEST_PYTHON_FILE, "line": 45},
    ]


@pytest.fixture
def mock_rules() -> List[Dict[str, Any]]:
    """Sample rules data for testing"""
    return [
        {
            "rule_id": 0,
            "name": "Unused Import",
            "Description": "Remove unused imports",
            "language": "python",
            "parameters": {},
        },
        {
            "rule_id": 1,
            "name": "Console Log",
            "description": "Replace console.log with proper logging",
            "language": "javascript",
            "parameters": {"level": "warning"},
        },
    ]


@pytest.fixture
def mock_api_response(mock_warnings, mock_rules) -> Dict[str, Any]:
    """Complete mock API response"""
    return {
        "analysis": {
            "repo_url": "https://github.com/test/repo",
            "warnings": mock_warnings,
        },
        "rules": mock_rules,
    }


@pytest.fixture
def mock_workspace(tmp_path) -> str:
    """Create a temporary workspace with test files"""
    # Create Python test file
    python_file = tmp_path / TEST_PYTHON_FILE
    python_file.write_text(
        """import os
import sys
import unused_module

def test_function():
    print("Debug message")
    x = 10
    y = 20
    return x + y

def another_function():
    # Line 10 - target line for warning
    result = test_function()
    return result * 2
"""
    )

    # Create JavaScript test file
    js_file = tmp_path / TEST_JS_FILE
    js_file.write_text(
        """const express = require('express');
const app = express();

function processData(data) {
    console.log('Processing:', data);  // Line 25
    return data.map(item => item * 2);
}

module.exports = { processData };
"""
    )

    return str(tmp_path)


@pytest.fixture
def mock_ollama_response() -> str:
    """Mock successful Ollama response"""
    return json.dumps({"original": "import unused_module", "fixed": ""})


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing"""
    with patch("ollama.Client") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {"content": '{"original": "import unused_module", "fixed": ""}'}
        }
        yield mock_client


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for API calls"""
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def test_args():
    """Mock command line arguments"""

    class Args:
        scan_id = "test-scan-123"
        host = "http://localhost:11434"
        model = "llama3.1:latest"
        stream = False
        verbose = False

    return Args()


@pytest.fixture
def temp_env_file(tmp_path) -> Generator[str, None, None]:
    """Create a temporary .env file for testing"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
OLLAMA_HOST=http://test-ollama:11434
OLLAMA_MODEL=test-model:latest
API_BASE_URL=http://test-api:8000/api
LOG_LEVEL=DEBUG
"""
    )

    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    yield str(env_file)

    os.chdir(old_cwd)


@pytest.fixture
def sample_code_snippet() -> str:
    """Sample code snippet for testing"""
    return """def example_function():
    # This is line 8
    import unnecessary_import  # Line 10 - warning here
    x = 10
    return x * 2"""


@pytest.fixture
def mock_prompt() -> str:
    """Sample prompt for testing"""
    return f"""Tu es un expert en correction de code python. \
Analyse ce problème et fournis une correction.

**Problème identifié :**
- Fichier : {TEST_PYTHON_FILE}
- Ligne : 10
- Règle : Unused Import
- Description : Remove unused imports

**Code concerné :**
```python
import unnecessary_import
```

**Instructions :**
1. Identifie la ligne exacte qui pose problème
2. Propose une correction qui respecte la règle
3. Réponds UNIQUEMENT au format JSON suivant \
(sans explication supplémentaire) :

{"original": "ligne de code originale problématique", \
"fixed": "ligne de code corrigée"}"""


@pytest.fixture
def capture_logs():
    """Fixture to capture log messages during tests"""
    from io import StringIO
    import logging

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)

    # Add handler to root logger
    root_logger = logging.getLogger()
    old_level = root_logger.level
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    yield log_capture

    # Cleanup
    root_logger.removeHandler(handler)
    root_logger.setLevel(old_level)


@pytest.fixture
def mock_json_responses() -> List[str]:
    """Various JSON response formats from AI for testing parsing"""
    return [
        # Clean JSON
        '{"original": "import unused", "fixed": ""}',
        # JSON with extra text
        (
            'Here is the fix:\n{"original": "print(x)", "fixed": "logger.info(x)"}'
            "\nThis removes the print statement."
        ),
        # Malformed but recoverable
        (
            'The solution is {"original": "console.log(data)", '
            '"fixed": "logger.debug(data)"}'
        ),
    ]
