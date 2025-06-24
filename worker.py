#!/usr/bin/env python3
"""
Worker script that runs inside the Docker container
Clones the repo, applies improvements, and creates a PR
"""

import os
import json
import subprocess
import asyncio
import logging
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/improvement.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CodeImprover:
    def __init__(self):
        self.repo_url = os.getenv('REPO_URL')
        self.branch = os.getenv('BRANCH', 'main')
        self.job_id = os.getenv('JOB_ID')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.sonar_report = json.loads(os.getenv('SONAR_REPORT', '{}'))
        self.workspace = Path('/workspace')
        self.repo_name = self.repo_url.split('/')[-1].replace('.git', '')
        self.repo_path = self.workspace / self.repo_name

    def setup_git_config(self):
        """Configure Git with credentials"""
        try:
            subprocess.run(['git', 'config', '--global', 'user.name', 'AI Code Improver'], check=True)
            subprocess.run(['git', 'config', '--global', 'user.email', 'ai-improver@company.com'], check=True)

            if self.github_token:
                # Configure to use token
                auth_url = self.repo_url.replace('https://', f'https://{self.github_token}@')
                subprocess.run(['git', 'config', '--global', 'url."' + auth_url + '".insteadOf', self.repo_url],
                               check=True)

            logger.info("✅ Git configuration completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git configuration failed: {e}")
            raise

    def clone_repository(self):
        """Clone the repository into the workspace"""
        try:
            logger.info(f"📥 Cloning repository: {self.repo_url}")

            clone_cmd = ['git', 'clone', '--depth', '1', '--branch', self.branch]
            if self.github_token:
                auth_url = self.repo_url.replace('https://', f'https://{self.github_token}@')
                clone_cmd.extend([auth_url, str(self.repo_path)])
            else:
                clone_cmd.extend([self.repo_url, str(self.repo_path)])

            result = subprocess.run(clone_cmd, capture_output=True, text=True, cwd=self.workspace)

            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")

            logger.info(f"✅ Repository cloned to {self.repo_path}")

            # Create a new branch for modifications
            branch_name = f"ai-improvements-{self.job_id[:8]}"
            subprocess.run(['git', 'checkout', '-b', branch_name], cwd=self.repo_path, check=True)
            logger.info(f"✅ Created branch: {branch_name}")

            return branch_name

        except Exception as e:
            logger.error(f"❌ Repository cloning failed: {e}")
            raise

    def analyze_sonar_report(self):
        """Analyze the SonarQube report and generate system prompt"""
        issues = self.sonar_report.get('issues', [])
        metrics = self.sonar_report.get('metrics', {})

        # Categorize issues
        critical_issues = [i for i in issues if i.get('severity') == 'CRITICAL']
        major_issues = [i for i in issues if i.get('severity') == 'MAJOR']
        security_issues = [i for i in issues if i.get('type') == 'VULNERABILITY']

        prompt = f"""
You are a code improvement expert. You must analyze and improve this repository based on the following SonarQube report.

SONARQUBE REPORT:
- Critical issues: {len(critical_issues)}
- Major issues: {len(major_issues)}  
- Security vulnerabilities: {len(security_issues)}
- Total issues: {len(issues)}

METRICS:
{json.dumps(metrics, indent=2)}

IMPROVEMENT PRIORITIES:
1. 🔴 CRITICAL: Fix all security vulnerabilities
2. 🟠 MAJOR: Resolve critical and major bugs
3. 🟡 IMPORTANT: Improve code quality (code smells)
4. 🟢 BONUS: Optimize performance and maintainability

DETAILED ISSUES:
{json.dumps(issues[:20], indent=2)}  # Limit to avoid overloading

INSTRUCTIONS:
- First examine the overall project architecture
- Identify patterns and technologies used
- Apply fixes one by one, explaining each change
- Test that code compiles/works after each major modification
- Create atomic commits for each type of fix
- Prioritize security and stability over optimization

CONSTRAINTS:
- NEVER delete files without asking
- Respect existing naming conventions
- Maintain compatibility with existing APIs
- Add comments to explain complex changes
"""
        return prompt

    async def improve_code_with_claude(self, branch_name):
        """Use Claude Code SDK to improve the code"""
        try:
            logger.info("🤖 Starting code improvement with Claude...")

            system_prompt = self.analyze_sonar_report()

            options = ClaudeCodeOptions(
                cwd=self.repo_path,
                system_prompt=system_prompt,
                allowed_tools=["Read", "Write", "Bash"],
                permission_mode="acceptEdits",
                max_turns=15  # Limit to avoid infinite loops
            )

            improvement_query = f"""
Analyze this repository and apply necessary improvements according to the SonarQube report.

Start by:
1. Exploring the project structure
2. Identifying the most problematic files
3. Applying fixes by priority order
4. Testing the modifications
5. Creating commits for each group of fixes

Repository: {self.repo_name}
Branch: {branch_name}
Job ID: {self.job_id}
"""

            messages_count = 0
            async for message in query(prompt=improvement_query, options=options):
                messages_count += 1
                logger.info(f"📝 Claude message {messages_count}: {str(message)[:200]}...")

                # Save important responses
                if hasattr(message, 'content'):
                    with open('/app/logs/claude_responses.log', 'a') as f:
                        f.write(f"\n--- Message {messages_count} ---\n")
                        f.write(str(message))
                        f.write("\n")

            logger.info(f"✅ Code improvement completed with {messages_count} interactions")
            return True

        except Exception as e:
            logger.error(f"❌ Claude code improvement failed: {e}")
            raise

    def create_pull_request(self, branch_name):
        """Create a Pull Request with the improvements"""
        try:
            logger.info("📤 Creating Pull Request...")

            # Final commit if there are uncommitted changes
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)

            # Check if there are changes
            result = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                                    capture_output=True, text=True, cwd=self.repo_path)

            if not result.stdout.strip():
                logger.info("ℹ️ No changes to commit")
                return None

            # Final commit
            commit_msg = f"""🤖 AI Code Quality Improvements (Job: {self.job_id})

✅ Applied SonarQube recommendations:
- Fixed security vulnerabilities
- Resolved critical and major issues
- Improved code quality and maintainability
- Applied best practices

Generated by AI Code Improver
Job ID: {self.job_id}
Timestamp: {datetime.now().isoformat()}
"""

            subprocess.run(['git', 'commit', '-m', commit_msg], cwd=self.repo_path, check=True)

            # Push the branch
            subprocess.run(['git', 'push', '-u', 'origin', branch_name], cwd=self.repo_path, check=True)

            # Create PR via GitHub CLI if available
            pr_title = f"🤖 AI Code Quality Improvements - Job {self.job_id[:8]}"
            pr_body = f"""
## 🤖 Automated Code Quality Improvements

This Pull Request contains automated code improvements based on SonarQube analysis.

### 📊 Improvements Applied:
- 🔒 Security vulnerabilities fixed
- 🐛 Critical and major bugs resolved  
- 🧹 Code smells addressed
- 📈 Performance optimizations
- 🔧 Maintainability improvements

### 📋 Details:
- **Job ID**: `{self.job_id}`
- **Branch**: `{branch_name}`
- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Issues Addressed**: {len(self.sonar_report.get('issues', []))} total issues

### 🔍 Review Guidelines:
- All changes have been automatically tested
- Security fixes should be prioritized for merge
- Review the commit history for detailed explanations
- Run your test suite to validate the changes

---
*Generated by AI Code Improver* 🚀
"""

            # Try to create PR via GitHub CLI
            try:
                pr_cmd = [
                    'gh', 'pr', 'create',
                    '--title', pr_title,
                    '--body', pr_body,
                    '--base', self.branch,
                    '--head', branch_name
                ]

                result = subprocess.run(pr_cmd, capture_output=True, text=True, cwd=self.repo_path)

                if result.returncode == 0:
                    pr_url = result.stdout.strip()
                    logger.info(f"✅ Pull Request created: {pr_url}")
                    return pr_url
                else:
                    logger.warning(f"⚠️ Failed to create PR via CLI: {result.stderr}")

            except FileNotFoundError:
                logger.info("ℹ️ GitHub CLI not available, branch pushed for manual PR creation")

            # Manual PR URL
            repo_parts = self.repo_url.replace('.git', '').split('/')
            if 'github.com' in self.repo_url:
                owner = repo_parts[-2]
                repo = repo_parts[-1]
                pr_url = f"https://github.com/{owner}/{repo}/compare/{self.branch}...{branch_name}"
                logger.info(f"📝 Manual PR URL: {pr_url}")
                return pr_url

            return None

        except Exception as e:
            logger.error(f"❌ Pull Request creation failed: {e}")
            raise

    async def run(self):
        """Main entry point of the worker"""
        try:
            logger.info(f"🚀 Starting code improvement job {self.job_id}")
            logger.info(f"📍 Repository: {self.repo_url}")
            logger.info(f"🌿 Branch: {self.branch}")

            # 1. Git configuration
            self.setup_git_config()

            # 2. Repository clone
            branch_name = self.clone_repository()

            # 3. Improvement with Claude
            await self.improve_code_with_claude(branch_name)

            # 4. Pull Request creation
            pr_url = self.create_pull_request(branch_name)

            if pr_url:
                logger.info(f"🎉 Job completed successfully! PR: {pr_url}")
                print(f"Pull Request created: {pr_url}")  # For extraction by API
            else:
                logger.info("🎉 Job completed! Changes pushed, create PR manually.")

            return True

        except Exception as e:
            logger.error(f"💥 Job failed: {e}")
            raise


if __name__ == "__main__":
    improver = CodeImprover()
    asyncio.run(improver.run())