# 🤖 Ollama CLI Tools

Simple command-line tools for interacting with Ollama AI models.

## 📋 Prerequisites

- Python 3.7+
- Ollama installed and running

## ⚡ Installation

```bash
git clone git@github.com:pre-msc-2027/ai.git
cd ai
pip install -r requirements.txt
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
- `-h, --host URL` - Ollama server URL (default: http://10.0.0.1:11434)
- `-m, --model MODEL` - Model to use (default: mistral:latest)
- `--stream` - Enable streaming output
- `--async` - Use asynchronous mode

**Examples:**
```bash
# Basic usage
python cli.py "What is Python?"

# Different model and host
python cli.py "Explain Docker" -m llama3:8b --host http://localhost:11434

# Streaming mode
python cli.py "Write a function to sort a list" -s

# Async mode
python cli.py "Explain machine learning" --async
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
- `-h, --host URL` - Ollama server URL (default: http://10.0.0.1:11434)
- `-m, --model MODEL` - Model to use (default: mistral:latest)
- `-s, --stream` - Enable streaming output
- `-v, --verbose` - Enable verbose output
- `-o, --output` - Save analysis to markdown files
- `--output-dir DIR` - Directory to save markdown files (created if not exists)
- `--async` - Force asynchronous mode (auto-enabled for multiple files)
- `--concurrent N` - Max concurrent requests in async mode (default: 3)

**Examples:**
```bash
# Analyze single file
python cli_file.py main.py

# Analyze multiple files (auto-async)
python cli_file.py src/*.py

# Save to markdown
python cli_file.py main.py -o

# Save to specific directory
python cli_file.py src/*.py -o --output-dir reports

# Custom model and concurrent processing
python cli_file.py *.py -m llama3:8b --concurrent 5

# Verbose output with streaming
python cli_file.py app.py -v -s
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