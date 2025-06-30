#!/bin/bash

# ========================================
# Complete deployment and testing script
# ========================================

echo "🚀 Deploying AI Code Improvement System"

# 1. Build Docker worker image
echo "📦 Building Docker image..."
docker build -t code-quality-improver:latest -f Dockerfile.worker .

# 2. Install API dependencies
echo "🐍 Installing API dependencies..."
pip install fastapi uvicorn docker python-multipart

# 3. Configure environment variables
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GITHUB_TOKEN="your-github-token"

# 4. Start API in background
echo "🌐 Starting API server..."
python api_server.py &
API_PID=$!

# Wait for API to start
sleep 5

# 5. Test health check
echo "🔍 Testing health check..."
curl -s http://localhost:8000/health | python -m json.tool

# 6. Test with sample SonarQube report
echo "📊 Sending test report..."

curl -X POST "http://localhost:8000/improve-code" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/your-username/test-repo.git",
    "branch": "main",
    "github_token": "'$GITHUB_TOKEN'",
    "priority": "high",
    "issues": [
      {
        "key": "security:S2068",
        "severity": "CRITICAL",
        "type": "VULNERABILITY",
        "message": "Hard-coded credentials detected",
        "file": "src/config.py",
        "line": 15
      },
      {
        "key": "bug:S1481",
        "severity": "MAJOR",
        "type": "BUG",
        "message": "Unused local variable",
        "file": "src/utils.py",
        "line": 42
      }
    ],
    "metrics": {
      "coverage": 65.4,
      "duplicated_lines_density": 12.3,
      "maintainability_rating": "C"
    }
  }' | python -m json.tool

echo ""
echo "✅ Test request sent! Check the API logs for progress."
echo ""
echo "🔗 Useful endpoints:"
echo "  - Health: http://localhost:8000/health"
echo "  - All jobs: http://localhost:8000/jobs"
echo "  - Job status: http://localhost:8000/status/{job_id}"
echo "  - Job logs: http://localhost:8000/logs/{job_id}"
echo ""
echo "📝 To stop the API: kill $API_PID"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    kill $API_PID 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

# Monitor jobs in real-time
echo "📊 Monitoring jobs (Ctrl+C to exit)..."
while true; do
    sleep 10
    echo "--- $(date) ---"
    curl -s http://localhost:8000/jobs | python -c "
import sys, json
data = json.load(sys.stdin)
for job in data['jobs']:
    print(f\"Job {job['job_id'][:8]}: {job['status']} - {job['repo_url']}\")
if not data['jobs']:
    print('No jobs yet')
"
done