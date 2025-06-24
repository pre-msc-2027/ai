from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
import docker
import asyncio
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
import os
from pathlib import Path

# Configuration
app = FastAPI(title="Code Quality Improvement API")
docker_client = docker.from_env()
logger = logging.getLogger(__name__)


# Pydantic Models
class SonarReport(BaseModel):
    repo_url: HttpUrl
    branch: str = "main"
    github_token: Optional[str] = None
    issues: List[Dict] = []
    metrics: Dict = {}
    priority: str = "medium"  # low, medium, high, critical


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    repo_url: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    logs: List[str] = []
    pull_request_url: Optional[str] = None
    error_message: Optional[str] = None


# In-memory job storage (replace with Redis/DB in production)
jobs_storage: Dict[str, JobStatus] = {}


@app.post("/improve-code")
async def trigger_code_improvement(
        report: SonarReport,
        background_tasks: BackgroundTasks
):
    """
    Main endpoint that receives a SonarQube report and triggers code improvement
    """
    job_id = str(uuid.uuid4())

    # Create the job
    job = JobStatus(
        job_id=job_id,
        status="pending",
        repo_url=str(report.repo_url),
        created_at=datetime.now()
    )
    jobs_storage[job_id] = job

    # Launch background processing
    background_tasks.add_task(process_code_improvement, job_id, report)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Code improvement job started",
        "status_url": f"/status/{job_id}"
    }


async def process_code_improvement(job_id: str, report: SonarReport):
    """
    Function that launches the Docker container to process the code
    """
    job = jobs_storage[job_id]

    try:
        job.status = "running"
        job.logs.append(f"Starting code improvement for {report.repo_url}")

        # Container configuration
        container_config = {
            "image": "code-quality-improver:latest",
            "environment": {
                "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
                "GITHUB_TOKEN": report.github_token or os.getenv("GITHUB_TOKEN"),
                "REPO_URL": str(report.repo_url),
                "BRANCH": report.branch,
                "JOB_ID": job_id,
                "SONAR_REPORT": json.dumps(report.dict())
            },
            "volumes": {
                f"/tmp/code-jobs/{job_id}": {"bind": "/workspace", "mode": "rw"},
                f"/tmp/logs/{job_id}": {"bind": "/app/logs", "mode": "rw"}
            },
            "working_dir": "/workspace",
            "detach": True,
            "auto_remove": True,
            "name": f"code-improver-{job_id}"
        }

        # Create directories
        os.makedirs(f"/tmp/code-jobs/{job_id}", exist_ok=True)
        os.makedirs(f"/tmp/logs/{job_id}", exist_ok=True)

        job.logs.append("Launching Docker container...")

        # Launch the container
        container = docker_client.containers.run(**container_config)

        # Wait for container completion
        result = container.wait()

        # Read logs
        logs = container.logs().decode('utf-8')
        job.logs.extend(logs.split('\n'))

        if result['StatusCode'] == 0:
            job.status = "completed"
            job.completed_at = datetime.now()

            # Search for PR URL in logs
            pr_url = extract_pr_url_from_logs(logs)
            if pr_url:
                job.pull_request_url = pr_url

            job.logs.append("✅ Code improvement completed successfully!")
        else:
            job.status = "failed"
            job.error_message = f"Container exited with code {result['StatusCode']}"
            job.logs.append(f"❌ Container failed with exit code {result['StatusCode']}")

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.logs.append(f"❌ Error: {str(e)}")
        logger.error(f"Job {job_id} failed: {str(e)}")


def extract_pr_url_from_logs(logs: str) -> Optional[str]:
    """
    Extract Pull Request URL from logs
    """
    import re
    pr_pattern = r"Pull Request created: (https://github\.com/[^\s]+)"
    match = re.search(pr_pattern, logs)
    return match.group(1) if match else None


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get job status
    """
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs_storage[job_id]


@app.get("/jobs")
async def list_jobs():
    """
    List all jobs
    """
    return {
        "jobs": list(jobs_storage.values()),
        "total": len(jobs_storage)
    }


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a running job
    """
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_storage[job_id]

    if job.status == "running":
        try:
            # Stop the container
            container = docker_client.containers.get(f"code-improver-{job_id}")
            container.stop()
            job.status = "cancelled"
            job.logs.append("Job cancelled by user")
            return {"message": "Job cancelled successfully"}
        except docker.errors.NotFound:
            job.status = "failed"
            job.error_message = "Container not found"
            return {"message": "Container not found, marked as failed"}

    return {"message": f"Job is in {job.status} state, cannot cancel"}


@app.get("/logs/{job_id}")
async def get_job_logs(job_id: str):
    """
    Get job logs
    """
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_storage[job_id]

    # Real-time logs from file
    log_file = f"/tmp/logs/{job_id}/improvement.log"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            file_logs = f.read().split('\n')
        return {"logs": job.logs + file_logs}

    return {"logs": job.logs}


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Check Docker
        docker_client.ping()

        # Check that image exists
        docker_client.images.get("code-quality-improver:latest")

        return {
            "status": "healthy",
            "docker": "connected",
            "image": "available",
            "active_jobs": len([j for j in jobs_storage.values() if j.status == "running"])
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create necessary directories
    os.makedirs("/tmp/code-jobs", exist_ok=True)
    os.makedirs("/tmp/logs", exist_ok=True)

    # Launch the API
    uvicorn.run(app, host="0.0.0.0", port=8000)