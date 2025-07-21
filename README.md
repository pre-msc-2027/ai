# 🤖 SecuScan AI

Simple command-line tools to generate analysis reports using Ollama models.

## 📋 Prerequisites

- Python 3.8+
- Ollama installed and running

## ⚡ Installation

```bash
git clone git@github.com:pre-msc-2027/ai.git
cd ai
poetry install
```

## 🛠️ Tools

### ollama_chat.py - Simple Ollama Chat

Interactive tool for sending prompts to Ollama models.

**Usage:**
```bash
python ollama_chat.py "Your prompt here" [options]
```

**Arguments:**
- `prompt` - Text prompt to send to the AI (required)

**Options:**
- `--host URL` - Ollama server URL (default: http://10.0.0.1:11434)
- `-m, --model MODEL` - Model to use (default: mistral:latest)
- `--stream` - Enable streaming output
- `-v, --verbose` - Enable verbose output (debug logs)

**Examples:**
```bash
# Basic usage
poetry run python ollama_chat.py "What is Python?"

# Different model and host
poetry run python ollama_chat.py "Explain Docker" -m llama3:8b --host http://localhost:11434

# Streaming mode
poetry run python ollama_chat.py "Write a function to sort a list" --stream

# Verbose mode (shows debug logs)
poetry run python ollama_chat.py "Debug this code" --verbose
```

### ollama_analyze.py - Code File Analysis

Tool for analyzing code files and generating improvement recommendations.

**Usage:**
```bash
python ollama_analyze.py file1 [file2 ...] [options]
```

**Arguments:**
- `file` - Path(s) to file(s) to analyze (supports glob patterns like `src/*.py`)

**Options:**
- `--host URL` - Ollama server URL (default: http://10.0.0.1:11434)
- `-m, --model MODEL` - Model to use (default: mistral:latest)
- `--stream` - Enable streaming output
- `-v, --verbose` - Enable verbose output
- `-o, --output` - Save analysis to markdown files
- `--output-dir DIR` - Directory to save markdown files (created if not exists)
- `--concurrent N` - Max concurrent requests for multiple files (default: 4)

**Examples:**
```bash
# Analyze single file
poetry run python ollama_analyze.py main.py

# Analyze multiple files (automatically uses async mode)
poetry run python ollama_analyze.py src/*.py

# Save to markdown
poetry run python ollama_analyze.py main.py -o

# Save to specific directory
poetry run python ollama_analyze.py src/*.py -o --output-dir reports

# Custom model and concurrent processing
poetry run python ollama_analyze.py *.py -m llama3:8b --concurrent 5

# Verbose output with streaming
poetry run python ollama_analyze.py app.py -v --stream
```

### ollama_workspace.py - Workspace File Management

Interactive tool for AI-assisted file management within a secure workspace using Ollama's function calling capabilities.

**Usage:**
```bash
python ollama_workspace.py workspace prompt [options]
```

**Arguments:**
- `workspace` - Path to the workspace directory (repository root)
- `prompt` - Initial prompt/request for the AI

**Options:**
- `--host URL` - Ollama server URL (default: http://10.0.0.1:11434)
- `-m, --model MODEL` - Model to use (default: llama3.1:latest)
- `--max-iterations N` - Max conversation rounds (default: 10)
- `-v, --verbose` - Enable verbose output

**Examples:**
```bash
# Create a new README file
poetry run python ollama_workspace.py /path/to/repo "Create a README.md with project overview"

# List and analyze Python files
poetry run python ollama_workspace.py . "Show me all Python files and their purpose"

# Refactor code
poetry run python ollama_workspace.py ./src "Help me refactor the authentication module"

# Interactive file management
poetry run python ollama_workspace.py /workspace "I need to reorganize the project structure"
```

**Available Tools:**
- `read_file(file_path)` - Read file content
- `write_file(file_path, content)` - Create/update files
- `list_files(directory, pattern)` - List files with patterns
- `create_directory(dir_path)` - Create directories
- `delete_file(file_path)` - Delete files/directories
- `append_to_file(file_path, content)` - Append content
- `find_files(name_pattern, content_pattern)` - Search files
- `get_workspace_info()` - Get workspace statistics

**Security Features:**
- All operations confined to specified workspace
- Path validation prevents directory traversal
- Detailed operation logging
- Safe error handling

**Requirements:**
- Ollama 0.4+ with a model supporting function calling (e.g., Llama 3.1)
```

## 📄 Output

### ollama_chat.py
Outputs the AI response directly to the console.

### ollama_analyze.py
- **Console**: Displays analysis results with code issues and recommendations
- **Markdown files** (with `-o`): Saves detailed reports with format `filename_analysis_YYYY_MM_DD-HH_MM_SS.md`

### ollama_workspace.py
- **Interactive mode**: Real-time conversation with AI for file operations
- **Tool feedback**: Shows each tool call and its result
- **Operation logs**: Detailed logging of all file operations

## ⚙️ Configuration

All tools support:
- Custom Ollama server URLs via `--host`
- Different AI models via `--model`
- Streaming vs. batch responses

## 🔧 Troubleshooting

**Connection issues:**
- Ensure Ollama is running: `ollama serve`
- Check the correct host/port with `--host`

**Model not found:**
- List available models: `ollama list`
- Pull a model: `ollama pull mistral:latest`

**File analysis issues:**
- Ensure files exist and are readable
- Check file extensions are supported (.py, .js, .ts, .java, etc.)

**Workspace management issues:**
- Ensure workspace directory exists and is accessible
- Check Ollama model supports function calling (e.g., Llama 3.1)
- Verify file permissions for read/write operations

## 🧪 Development & Testing

### Setup Development Environment

```bash
# Quick setup with script
./setup.sh

# Or manually:
poetry install --with dev
poetry run pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_cli.py

# Run tests in verbose mode
poetry run pytest -v
```

### Test Structure

- `tests/` - Test directory
- `tests/conftest.py` - Common fixtures and test utilities
- `tests/test_ollama_chat.py` - Tests for ollama_chat.py functionality
- `tests/test_ollama_analyze.py` - Tests for ollama_analyze.py functionality
- `tests/test_ollama_workspace.py` - Tests for ollama_workspace.py functionality

### Coverage Reports

HTML coverage reports are generated in `htmlcov/` directory after running tests with `--cov` flag.

### Code Quality

Pre-commit hooks run automatically on every commit to ensure code quality:
- **Black**: Code formatting (88 char line length)
- **isort**: Import sorting
- **Flake8**: Linting
- **Mypy**: Type checking
- File cleanup (trailing whitespace, EOF, etc.)

To run all checks manually:
```bash
poetry run pre-commit run --all-files
```
