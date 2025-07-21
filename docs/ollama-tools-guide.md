# Ollama Tools Guide for File Management

This document describes how to implement file management tools with Ollama using the "tools" (function calling) system.

## Overview

Ollama supports "tool calling" since version 0.4 of the Python library, allowing models to interact with external Python functions. This enables creating AI assistants capable of manipulating files within a secure workspace.

## Supported Models

- Llama 3.1 and higher versions
- Mistral Nemo
- Other recent models with native tool support

## Tool Structure

### Method 1: Direct Python Function (Recommended)

```python
def read_file(file_path: str) -> str:
    """
    Read the content of a file in the workspace

    Args:
        file_path: Relative path of the file in the workspace

    Returns:
        str: File content

    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If access is denied
    """
    # File validation and reading logic
    pass
```

**Usage:**
```python
response = ollama.chat(
    'llama3.1',
    messages=[{'role': 'user', 'content': 'Read the README.md file'}],
    tools=[read_file]  # Direct function reference
)
```

### Method 2: JSON Schema Definition

```python
tools = [{
    'type': 'function',
    'function': {
        'name': 'read_file',
        'description': 'Read the content of a file in the workspace',
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'Relative path of the file in the workspace',
                },
            },
            'required': ['file_path'],
        },
    },
}]
```

## Proposed File Management Tools

### 1. File Reading

```python
def read_file(file_path: str) -> str:
    """Read the content of a file"""
    pass

def list_files(directory: str = "", pattern: str = "*") -> List[Dict]:
    """List files in a directory"""
    pass
```

### 2. File Writing

```python
def write_file(file_path: str, content: str, create_dirs: bool = True) -> bool:
    """Write content to a file"""
    pass

def append_to_file(file_path: str, content: str) -> bool:
    """Append content to the end of a file"""
    pass
```

### 3. Directory Management

```python
def create_directory(dir_path: str) -> bool:
    """Create a directory"""
    pass

def delete_file(file_path: str) -> bool:
    """Delete a file or directory"""
    pass
```

### 4. Workspace Information

```python
def get_workspace_info() -> Dict[str, Any]:
    """Get information about the workspace"""
    pass

def find_files(pattern: str, content_pattern: str = None) -> List[str]:
    """Search files by name or content"""
    pass
```

## Processing Tool Calls

```python
# Dictionary of available functions
available_functions = {
    'read_file': read_file,
    'write_file': write_file,
    'list_files': list_files,
    'create_directory': create_directory,
    'delete_file': delete_file,
}

# Processing model response
response = ollama.chat(model, messages, tools=list(available_functions.values()))

for tool_call in response.message.tool_calls or []:
    function_name = tool_call.function.name
    function_args = tool_call.function.arguments

    if function_name in available_functions:
        try:
            result = available_functions[function_name](**function_args)
            print(f"Result of {function_name}: {result}")
        except Exception as e:
            print(f"Error executing {function_name}: {e}")
    else:
        print(f"Unknown function: {function_name}")
```

## Security and Validation

### Path Validation

```python
class WorkspaceManager:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    def _validate_path(self, file_path: str) -> Path:
        """Validate that a path is within the workspace"""
        path = Path(file_path)
        if path.is_absolute():
            resolved_path = path.resolve()
        else:
            resolved_path = (self.workspace_root / path).resolve()

        # Security check: path must be within workspace
        try:
            resolved_path.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError(f"Path outside workspace: {file_path}")

        return resolved_path
```

### Security Limitations

- All operations are confined to the defined workspace
- Strict path validation to prevent directory traversal
- Detailed logging of all operations
- Robust error handling with explicit messages

## Implementation Example

```python
import ollama
from pathlib import Path
from typing import List, Dict, Any

class FileToolsManager:
    def __init__(self, workspace_root: str):
        self.workspace = Path(workspace_root).resolve()

    def get_tools(self) -> List[callable]:
        """Return the list of available tools"""
        return [
            self.read_file,
            self.write_file,
            self.list_files,
            self.create_directory,
            self.delete_file,
        ]

    def chat_with_tools(self, model: str, user_message: str):
        """Start a conversation with file tools"""
        messages = [
            {
                "role": "system",
                "content": f"You are an AI assistant with access to file management tools in workspace: {self.workspace}"
            },
            {
                "role": "user",
                "content": user_message
            }
        ]

        response = ollama.chat(
            model=model,
            messages=messages,
            tools=self.get_tools()
        )

        return self._process_response(response)
```

## Best Practices

1. **Type Hints**: Use complete type annotations for better schema generation
2. **Docstrings**: Clearly document the purpose of each function
3. **Error Handling**: Implement robust error handling with explicit messages
4. **Validation**: Always validate inputs and file paths
5. **Logging**: Log all operations for debugging and auditing
6. **Security**: Strict workspace confinement to prevent unauthorized access

## Proposed Architecture

```
ollama_workspace.py
├── WorkspaceManager          # Secure workspace management
├── FileTools                 # Set of file tools
├── ConversationManager       # Tool conversation management
└── CLI Interface            # Command line interface
```

This guide will serve as the foundation for implementing the `ollama_workspace.py` module with Ollama tools for file management.
