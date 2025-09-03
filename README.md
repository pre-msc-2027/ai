# 🤖 SecuScan AI

AI-powered code analysis and fix generation tool that integrates with SonarQube-style static analysis APIs. Analyzes code warnings and provides intelligent fixes using Ollama models.

## 🎯 Overview

SecuScan AI is a command-line tool that:
- Fetches code analysis data from external APIs
- Processes warnings and rule violations using AI
- Generates precise code fixes in JSON format
- Supports multiple programming languages and rule sets
- Integrates seamlessly with existing CI/CD workflows

## 📋 Prerequisites

- Python 3.11+
- Ollama installed and running
- Access to a code analysis API (or use the provided test server)

## ⚡ Installation

```bash
git clone git@github.com:pre-msc-2027/ai.git
cd ai
poetry install
```

## 🛠️ Usage

### Basic Command

```bash
python -m src.main --scan-id <scan_identifier>
```

### Arguments

- `--scan-id` - **Required**: Identifier for the scan/analysis to process

### Options

- `--host URL` - Ollama server URL (default: `http://localhost:11434`)
- `--model MODEL` - AI model to use (default: `llama3.1:latest`)
- `--stream` - Enable streaming output (shows AI processing in real-time)
- `--verbose` - Enable detailed logging and debug information

### Examples

```bash
# Basic usage
python -m src.main --scan-id my-project-scan-001

# Custom Ollama server and model
python -m src.main --scan-id scan-123 --host http://192.168.0.1:11434 --model llama3.1:8b

# Streaming mode with verbose output
python -m src.main --scan-id scan-456 --stream --verbose

# Production usage
OLLAMA_HOST=http://production-ollama:11434 python -m src.main --scan-id prod-scan-789
```

## 📊 API Integration

### Expected API Response Format

The tool expects the analysis API to return data in this format:

```json
{
  "analysis": {
    "repo_url": "https://github.com/org/repo",
    "warnings": [
      {
        "id": 0,
        "rule_id": 1,
        "file": "src/main.py",
        "line": 42
      }
    ]
  },
  "rules": [
    {
      "rule_id": 1,
      "name": "Unused Import",
      "description": "Remove unused imports to clean up code",
      "language": "python",
      "parameters": {}
    }
  ]
}
```

### Test API Server

For development and testing, use the included test server:

```bash
# Start test API server
python scripts/test_api_server.py

# Server runs on http://localhost:8000
# Test with: python -m src.main --scan-id test-scan
```

### API Configuration

Set the API endpoint via environment variables:

```bash
export API_BASE_URL="https://your-analysis-api.com/api"
```

## 🏗️ Architecture

### Project Structure

```
src/
├── api/           # API client for fetching analysis data
│   ├── __init__.py
│   └── issues.py  # Main API integration
├── ollama/        # Ollama client abstraction
│   ├── __init__.py
│   └── client.py  # AI model communication
├── utils/         # Utility functions
│   ├── __init__.py
│   └── code_reader.py  # Code extraction and parsing
├── main.py        # Main CLI entry point
└── prompt_builder.py   # AI prompt generation

scripts/
└── test_api_server.py  # Development API server

tests/
└── unit/          # Unit tests
```

### Data Flow

1. **API Layer** (`src/api/`) fetches analysis data from external API
2. **Code Reader** (`src/utils/`) extracts relevant code snippets from files
3. **Prompt Builder** constructs AI prompts with context and rules
4. **Ollama Client** (`src/ollama/`) sends prompts to AI and processes responses
5. **Main CLI** orchestrates the process and outputs structured JSON results

### Output Format

The tool outputs JSON with original and fixed code:

```json
[
  {
    "warning_id": 0,
    "original": "import unused_module",
    "fixed": ""
  },
  {
    "warning_id": 1,
    "original": "print(debug_info)",
    "fixed": "logger.debug(debug_info)"
  }
]
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:latest

# API Configuration
API_BASE_URL=https://your-analysis-api.com/api

# Logging
LOG_LEVEL=INFO
```

### Supported Models

- **Llama 3.1** (recommended) - Best performance for code analysis
- **Mistral** - Good alternative with faster processing
- **CodeLlama** - Specialized for code understanding

## 💻 Development

### Setup Development Environment

```bash
# Install with development dependencies
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test module
poetry run pytest tests/unit/test_utils_code_reader.py

# Verbose output
poetry run pytest -v
```

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting (88 character limit)
- **isort**: Import sorting
- **Flake8**: Linting and style checking
- **MyPy**: Static type checking
- **Pre-commit**: Automated checks on commit

Run all quality checks:

```bash
poetry run pre-commit run --all-files
```

### Test Structure

- `tests/unit/` - Unit tests for individual modules
- `tests/unit/test_utils_code_reader.py` - Tests for code extraction utilities
- More test modules to be added for each component

## 🔧 Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Ollama server
```
❌ Error: Connection refused to http://localhost:11434
```

**Solutions**:
- Ensure Ollama is running: `ollama serve`
- Check the correct host with `--host` parameter
- Verify firewall settings

### Model Issues

**Problem**: Model not found error
```
❌ Model 'llama3.1:latest' not found
```

**Solutions**:
- List available models: `ollama list`
- Pull the required model: `ollama pull llama3.1:latest`
- Use an alternative model with `--model`

### API Issues

**Problem**: API endpoint not responding
```
❌ Failed to fetch analysis data for scan ID
```

**Solutions**:
- Verify API endpoint is accessible
- Check scan ID format and existence
- Use test server for development: `python scripts/test_api_server.py`

### Code Analysis Issues

**Problem**: No fixes generated for warnings
```
⚠️ Warning: No valid fixes generated
```

**Solutions**:
- Ensure code files exist and are readable
- Check if warnings point to valid file paths
- Verify AI model supports the programming language
- Try with `--verbose` for detailed processing logs

### Performance Issues

**Problem**: Slow processing with many warnings

**Solutions**:
- Use a faster model (e.g., smaller Llama variant)
- Enable streaming with `--stream` for real-time feedback
- Process scans in smaller batches
- Ensure adequate system resources for AI model

## 📈 Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: AI Code Analysis
  run: |
    python -m src.main --scan-id ${{ github.run_id }} > fixes.json
    # Process fixes.json for automated PRs or reports
```

### Custom API Integration

```python
# Custom wrapper example
import subprocess
import json

def analyze_with_ai(scan_id, model="llama3.1:latest"):
    cmd = ["python", "-m", "src.main", "--scan-id", scan_id, "--model", model]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)
```

---

## 📄 License

MIT
