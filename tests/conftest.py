"""
Common test fixtures for Ollama CLI tools
"""

import pytest
import tempfile
import os
from typing import Generator, AsyncGenerator, Iterator, List, Dict, Any
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def temp_file() -> Generator[str, None, None]:
    """Create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""#!/usr/bin/env python3
import os
import sys
# TODO: Remove unused import
import json

def test_function():
    # Print statement
    print("This is a test")
    # Long line that exceeds 120 characters limit and should be split for better readability according to style guidelines
    api_key = "secret_key_123"  # Hardcoded credential
    return True

try:
    result = test_function()
except:
    pass  # Empty catch block
""")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_ollama_client() -> Mock:
    """Mock Ollama client for testing"""
    mock_client = Mock()
    mock_response = {
        'message': {
            'content': 'Mock analysis response from Ollama'
        }
    }
    mock_client.chat.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_ollama_async_client() -> AsyncMock:
    """Mock async Ollama client for testing"""
    mock_client = AsyncMock()
    mock_response = {
        'message': {
            'content': 'Mock async analysis response from Ollama'
        }
    }
    mock_client.chat.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_streaming_response() -> Iterator[Dict[str, Any]]:
    """Mock streaming response from Ollama"""
    chunks = [
        {'message': {'content': 'Mock '}},
        {'message': {'content': 'streaming '}},
        {'message': {'content': 'response'}}
    ]
    return iter(chunks)


@pytest.fixture
def mock_async_streaming_response() -> AsyncGenerator[Dict[str, Any], None]:
    """Mock async streaming response from Ollama"""
    chunks = [
        {'message': {'content': 'Mock '}},
        {'message': {'content': 'async '}},
        {'message': {'content': 'streaming '}},
        {'message': {'content': 'response'}}
    ]
    
    async def async_generator() -> AsyncGenerator[Dict[str, Any], None]:
        for chunk in chunks:
            yield chunk
    
    return async_generator()


@pytest.fixture
def sample_static_issues() -> List[Dict[str, Any]]:
    """Sample static analysis issues for testing"""
    return [
        {
            'line': 5,
            'type': 'code_smell',
            'severity': 'INFO',
            'message': 'Complete the task associated to this TODO comment',
            'code': '# TODO: Remove unused import'
        },
        {
            'line': 9,
            'type': 'code_smell', 
            'severity': 'MINOR',
            'message': 'Replace this use of System.out or System.err by a logger',
            'code': 'print("This is a test")'
        },
        {
            'line': 11,
            'type': 'vulnerability',
            'severity': 'BLOCKER', 
            'message': 'Review this hardcoded credential',
            'code': 'api_key = "secret_key_123"'
        }
    ]