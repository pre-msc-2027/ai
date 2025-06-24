# TODO - Claude AI CLI Tool

## Phase 1: Base Structure and Configuration ✓ In Progress

### 1. Create TODO.md file ✓
- [x] Define project phases
- [x] Establish priorities and dependencies

### 2. Create base structure of cli.py
- [ ] Import necessary dependencies
  - `argparse` for CLI argument handling
  - `json` for JSON file manipulation
  - `os` and `sys` for system operations
  - `pathlib` for path management
  - `claude-code-sdk` for Claude integration
- [ ] Create main `ClaudeCLI` class
- [ ] Define command structure with argparse
- [ ] Add global error handling
- [ ] Implement configuration loading

## Phase 2: Analysis Commands

### 3. Implement analyze-repo command
- [ ] Create `analyze_repository()` function
- [ ] Parameters to handle:
  - `--url`: GitHub repository URL (required)
  - `--token`: GitHub token (optional)
  - `--type`: Analysis type (quick, comprehensive, security, performance, style)
  - `--output`: Output file (optional)
  - `--format`: Output format (json, text, markdown)
- [ ] Integrate with GitHub API to clone/access repository
- [ ] Call Claude AI for analysis
- [ ] Format and save results

### 4. Implement analyze-json command
- [ ] Create `analyze_from_json()` function
- [ ] Parse JSON configuration file
- [ ] Validate JSON structure
- [ ] Extract parameters:
  - Repository info (url, token)
  - Analysis settings (type, focus_areas, max_files, exclude_patterns)
  - Output settings (format, file)
- [ ] Reuse logic from `analyze_repository()`

### 5. Implement analyze-local command
- [ ] Create `analyze_local_directory()` function
- [ ] Parameters:
  - `--path`: Local directory path
  - `--include`: File patterns to include
  - `--exclude`: File patterns to exclude
  - `--type`: Analysis type
- [ ] Scan local directory
- [ ] Filter files according to patterns
- [ ] Analyze with Claude AI

### 6. Implement analyze-code command
- [ ] Create `analyze_code_snippet()` function
- [ ] Parameters:
  - `--file`: File containing code
  - `--stdin`: Read from stdin
  - `--language`: Programming language
- [ ] Read code from file or stdin
- [ ] Auto-detect language if not specified
- [ ] Analyze with Claude AI

## Phase 3: Integration and Formatting

### 7. Claude AI Integration
- [ ] Create `claude_integration.py` module
- [ ] Implement `ClaudeAnalyzer` class
- [ ] Handle API authentication
- [ ] Create specialized prompts for each analysis type:
  - Quick: Rapid analysis, obvious issues
  - Comprehensive: Complete and detailed analysis
  - Security: Focus on vulnerabilities
  - Performance: Possible optimizations
  - Style: Conventions and code readability
- [ ] Handle token limits and pagination

### 8. Output Formatting
- [ ] Create `output_formatter.py` module
- [ ] Implement formatters:
  - `JSONFormatter`: Structured JSON output
  - `TextFormatter`: Readable text output
  - `MarkdownFormatter`: Formatted Markdown report
- [ ] Templates for each format
- [ ] Severity level handling (high, medium, low)

## Phase 4: Configuration and Utilities

### 9. Configuration Management
- [ ] Create `config_manager.py` module
- [ ] Search for `.claude-config.json` in:
  - Current directory
  - User home directory
  - Path specified by environment variable
- [ ] Merge with CLI arguments (arguments take priority)
- [ ] Validate API keys

### 10. Utilities
- [ ] Create `utils.py` module
- [ ] Utility functions:
  - `validate_github_url()`
  - `extract_repo_info()`
  - `filter_files_by_pattern()`
  - `detect_language()`
  - `sanitize_output()`
- [ ] Cache management to avoid re-downloading repositories

## Phase 5: Testing and Documentation

### 11. Unit Tests
- [ ] Create `tests/` directory
- [ ] Tests for each module:
  - `test_cli.py`
  - `test_claude_integration.py`
  - `test_output_formatter.py`
  - `test_config_manager.py`
  - `test_utils.py`
- [ ] Use pytest
- [ ] Mocks for API calls

### 12. Documentation
- [ ] Docstrings for all functions
- [ ] Create `CONTRIBUTING.md`
- [ ] Advanced usage examples
- [ ] Troubleshooting guide

## Project Structure

```
ai/
├── cli.py                 # Main entry point
├── claude_integration.py  # Claude AI integration
├── output_formatter.py    # Result formatting
├── config_manager.py      # Configuration management
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_claude_integration.py
│   └── ...
├── examples/            # Configuration examples
│   ├── basic-analysis.json
│   ├── security-scan.json
│   └── comprehensive.json
└── .claude-config.json  # Default configuration (example)

```

## Dependencies to Install

```bash
# requirements.txt
claude-code-sdk>=1.0.0
argparse>=1.4.0
requests>=2.31.0
pygithub>=2.1.1
pytest>=7.4.0
pytest-mock>=3.12.0
```

## Recommended Implementation Order

1. **cli.py** - Base structure with argparse
2. **config_manager.py** - To manage configuration from the start
3. **claude_integration.py** - Core analysis functionality
4. **analyze-repo** - First complete command
5. **output_formatter.py** - To see results
6. Other commands in priority order
7. Tests in parallel with development

## Notes

- Start with minimal viable product (MVP) for each command
- Add advanced features incrementally
- Ensure proper error handling at each step
- Consider rate limiting for API calls
- Implement proper logging for debugging