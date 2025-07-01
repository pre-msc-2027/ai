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

### cli.py - Simple Ollama Chat

Interactive tool for sending prompts to Ollama models.

**Usage:**
```bash
python cli.py "Your prompt here" [options]
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
poetry run python cli.py "What is Python?"

# Different model and host
poetry run python cli.py "Explain Docker" -m llama3:8b --host http://localhost:11434

# Streaming mode
poetry run python cli.py "Write a function to sort a list" --stream

# Verbose mode (shows debug logs)
poetry run python cli.py "Debug this code" --verbose
```

### cli_file.py - Code File Analysis

Tool for analyzing code files and generating improvement recommendations.

**Usage:**
```bash
python cli_file.py file1 [file2 ...] [options]
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
poetry run python cli_file.py main.py

# Analyze multiple files (automatically uses async mode)
poetry run python cli_file.py src/*.py

# Save to markdown
poetry run python cli_file.py main.py -o

# Save to specific directory
poetry run python cli_file.py src/*.py -o --output-dir reports

# Custom model and concurrent processing
poetry run python cli_file.py *.py -m llama3:8b --concurrent 5

# Verbose output with streaming
poetry run python cli_file.py app.py -v --stream
```

## 📄 Output

### cli.py
Outputs the AI response directly to the console.

### cli_file.py
- **Console**: Displays analysis results with code issues and recommendations
- **Markdown files** (with `-o`): Saves detailed reports with format `filename_analysis_YYYY_MM_DD-HH_MM_SS.md`

## ⚙️ Configuration

Both tools support:
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

## 🧪 Development & Testing

### Running Tests

With Poetry:
```bash
# Install dev dependencies
poetry install --with dev

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
- `tests/test_cli.py` - Tests for cli.py functionality
- `tests/test_cli_file.py` - Tests for cli_file.py functionality

### Coverage Reports

HTML coverage reports are generated in `htmlcov/` directory after running tests with `--cov` flag.