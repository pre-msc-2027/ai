# 🤖 AI Code Quality Improver

An automated code quality improvement system that analyzes code reports and uses Ollama AI to fix issues, improve code quality, and create pull requests automatically.

## 🚀 Features

- **Automated Code Analysis**: Processes code reports to identify critical issues
- **AI-Powered Fixes**: Uses Ollama to analyze and improve code
- **Docker Isolation**: Each repository is processed in its own isolated container
- **Git Integration**: Automatically clones repos, creates branches, and submits PRs
- **Real-time Monitoring**: REST API with job tracking and live logs
- **Security Priority**: Focuses on fixing vulnerabilities and critical bugs first

## 🏗️ Architecture

```
Code Report → API Server → Docker Container → Ollama model → Pull Request
```

1. **API Server**: Receives code reports via REST API
2. **Job Management**: Tracks improvement jobs with unique IDs
3. **Docker Workers**: Isolated containers that clone repos and apply fixes
4. **Ollama Integration**: Uses Ollama for intelligent code improvements
5. **GitHub Integration**: Creates branches and pull requests automatically

## 📋 Prerequisites

- Docker installed and running
- Python 3.11+
- Ollama installed and running (or access to Ollama server)

## ⚡ Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd ai-code-improver

# Install API dependencies
pip install fastapi uvicorn docker python-multipart
```

### 2. Build Docker Image

```bash
docker build -t code-quality-improver:latest -f Dockerfile.worker.worker .
```

### 3. Start the API Server

```bash
python api_server.py
```

The API will be available at `http://localhost:8000`

### 4. Submit a code Report

```bash
curl -X POST "http://localhost:8000/improve-code" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/your-org/your-repo.git",
    "branch": "main",
    "priority": "high",
    "issues": [
      {
        "key": "security:S2068",
        "severity": "CRITICAL",
        "type": "VULNERABILITY",
        "message": "Hard-coded credentials detected",
        "file": "src/config.py",
        "line": 15
      }
    ],
    "metrics": {
      "coverage": 65.4,
      "duplicated_lines_density": 12.3,
      "maintainability_rating": "C"
    }
  }'
```

## 📊 API Endpoints

| Endpoint           | Method | Description                         |
|--------------------|--------|-------------------------------------|
| `/improve-code`    | POST   | Submit a code report for processing |
| `/status/{job_id}` | GET    | Get job status and details          |
| `/jobs`            | GET    | List all jobs                       |
| `/logs/{job_id}`   | GET    | Get real-time job logs              |
| `/jobs/{job_id}`   | DELETE | Cancel a running job                |
| `/health`          | GET    | System health check                 |

## 🔧 Configuration

### code Report Format

```json
{
  "repo_url": "https://github.com/owner/repo.git",
  "branch": "main",
  "priority": "high|medium|low",
  "issues": [
    {
      "key": "rule-key",
      "severity": "CRITICAL|MAJOR|MINOR",
      "type": "BUG|VULNERABILITY|CODE_SMELL",
      "message": "Issue description",
      "file": "path/to/file.py",
      "line": 42
    }
  ],
  "metrics": {
    "coverage": 65.4,
    "duplicated_lines_density": 12.3,
    "maintainability_rating": "C"
  }
}
```

## 🐳 Docker Architecture

The system uses Docker containers to isolate each code improvement job:

- **Base Image**: Python 3.11 with Git, Node.js, and GitHub CLI
- **Ollama**: Installed for AI-powered code analysis
- **Isolated Workspace**: Each job runs in its own container and directory
- **Auto-cleanup**: Containers are automatically removed after completion

## 🔍 Job Lifecycle

1. **Pending**: Job created and queued
2. **Running**: Docker container launched, repo cloned
3. **Improving**: Ollama model analyzes and modifies code
4. **Completed**: Changes committed and PR created
5. **Failed**: Error occurred (check logs for details)

## 📝 Example Output

When a job completes successfully, you'll get:

```json
{
  "job_id": "abc123...",
  "status": "completed",
  "repo_url": "https://github.com/owner/repo.git",
  "pull_request_url": "https://github.com/owner/repo/pull/42",
  "completed_at": "2025-06-24T10:30:00Z"
}
```

## 🔒 Security Features

- **Isolated Execution**: Each repo is processed in a separate container
- **Permission Control**: Ollama model runs with limited tool permissions
- **Auto-cleanup**: Temporary files and containers are automatically removed

## 🚦 Best Practices

1. **Test First**: Try the system on a test repository before production use
2. **Review PRs**: Always review AI-generated changes before merging
3. **Backup Important Repos**: The system creates new branches, but backup critical code
4. **Monitor Jobs**: Use the logs endpoint to track progress and debug issues

## 🛠️ Development

### Running Tests

```bash
# Test the complete workflow
bash usage_example.sh
```

### Adding Custom Rules

Modify the `analyze_code_report()` function in `worker.py` to customize how issues are prioritized and processed.

### Extending the API

The FastAPI server can be easily extended with additional endpoints for webhooks, notifications, or custom integrations.

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the `/health` endpoint for system status
- Review job logs via `/logs/{job_id}`
- Open an issue on GitHub

---

**⚠️ Disclaimer**: This tool uses AI to modify code automatically. Always review changes before merging to production.