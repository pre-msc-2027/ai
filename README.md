# Claude AI CLI Tool

Simple command-line tool for analyzing code repositories using Claude AI.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Claude](https://img.shields.io/badge/Claude-Code%20SDK-orange.svg)](https://docs.anthropic.com/en/docs/claude-code/sdk)

## Installation

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Install Python dependencies
pip install claude-code-sdk
```

## Configuration

```bash
# Set your API keys
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GITHUB_TOKEN="your-github-token"  # Optional for public repos
```

## Usage

### Analyze GitHub Repository

```bash
# Basic repository analysis
python cli_docker.py analyze-repo --url https://github.com/user/repository

# With GitHub token
python cli_docker.py analyze-repo --url https://github.com/user/repository --token your-github-token

# Specify analysis type
python cli_docker.py analyze-repo --url https://github.com/user/repository --type security

# Save output to file
python cli_docker.py analyze-repo --url https://github.com/user/repository --output report.json
```

### Analyze from JSON Config

```bash
# Use JSON configuration file
python cli_docker.py analyze-json --config analysis-config.json
```

**Example JSON config:**
```json
{
  "repository": {
    "url": "https://github.com/user/repository",
    "token": "optional-github-token"
  },
  "analysis": {
    "type": "comprehensive",
    "focus_areas": ["security", "performance"],
    "max_files": 50,
    "exclude_patterns": ["*.min.js", "node_modules/*"]
  },
  "output": {
    "format": "json",
    "file": "analysis-report.json"
  }
}
```

### Analyze Local Directory

```bash
# Analyze local code
python cli_docker.py analyze-local --path /path/to/project

# With specific file types
python cli_docker.py analyze-local --path /path/to/project --include "*.py,*.js"
```

### Code Snippet Analysis

```bash
# Analyze code from file
python cli_docker.py analyze-code --file code-snippet.py --language python

# Analyze code from stdin
echo "print('hello world')" | python cli_docker.py analyze-code --language python --stdin
```

## Command Options

### Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--anthropic-key` | Anthropic API key | From env `ANTHROPIC_API_KEY` |
| `--claude-model` | Claude model to use | `claude-3-sonnet-20240229` |
| `--verbose` | Verbose output | `False` |

### Analysis Options

| Option | Description | Values |
|--------|-------------|--------|
| `--type` | Analysis type | `quick`, `comprehensive`, `security`, `performance`, `style` |
| `--output` | Output file | stdout if not specified |
| `--format` | Output format | `json`, `text`, `markdown` |

## Examples

### Basic Analysis

```bash
python cli_docker.py analyze-repo --url https://github.com/fastapi/fastapi --type security
```

### Comprehensive Analysis with Custom Output

```bash
python cli_docker.py analyze-repo \
  --url https://github.com/user/repo \
  --token ghp_xxxxxxxxxxxx \
  --type comprehensive \
  --output detailed-report.json \
  --format json
```

### Using Configuration File

```bash
# Create config file
cat > my-analysis.json << EOF
{
  "repository": {
    "url": "https://github.com/user/repository"
  },
  "analysis": {
    "type": "security",
    "focus_areas": ["vulnerabilities", "secrets"]
  },
  "output": {
    "file": "security-report.json"
  }
}
EOF

# Run analysis
python cli_docker.py analyze-json --config my-analysis.json
```

### Local Project Analysis

```bash
# Quick scan of current directory
python cli_docker.py analyze-local --path . --type quick

# Comprehensive analysis excluding certain files
python cli_docker.py analyze-local \
  --path /my/project \
  --type comprehensive \
  --exclude "*.min.js,node_modules/*,dist/*" \
  --output project-analysis.md \
  --format markdown
```

## Output Formats

### JSON Output
```json
{
  "repository": "https://github.com/user/repo",
  "analysis_date": "2025-01-15T10:30:00Z",
  "summary": "Analysis completed successfully",
  "issues": [
    {
      "type": "security",
      "severity": "high",
      "file": "src/auth.py",
      "line": 23,
      "message": "Hardcoded API key detected",
      "suggestion": "Use environment variables"
    }
  ],
  "recommendations": [
    "Add input validation",
    "Implement proper logging"
  ]
}
```

### Markdown Output
```markdown
# Code Analysis Report

**Repository:** https://github.com/user/repo
**Date:** 2025-01-15T10:30:00Z

## Summary
Analysis completed successfully

## Issues Found

### 🔴 High Priority
- **Security Issue** in `src/auth.py:23`
  - Hardcoded API key detected
  - **Suggestion:** Use environment variables

## Recommendations
- Add input validation
- Implement proper logging
```

## Configuration File

Create a `.claude-config.json` file for default settings:

```json
{
  "anthropic_api_key": "your-api-key",
  "github_token": "your-github-token",
  "default_model": "claude-3-sonnet-20240229",
  "default_analysis_type": "comprehensive",
  "output_format": "json"
}
```

## Help

```bash
# General help
python cli_docker.py --help

# Command-specific help
python cli_docker.py analyze-repo --help
python cli_docker.py analyze-json --help
python cli_docker.py analyze-local --help
python cli_docker.py analyze-code --help
```

## Requirements

- Python 3.10+
- Node.js (for Claude Code CLI)
- Anthropic API key
- GitHub token (optional, for private repos)

## License

MIT