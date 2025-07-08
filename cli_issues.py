#!/usr/bin/env python3
"""
Ollama AI CLI Tool - Issue and Rule Management with Predictable Responses
Handles code issues, rules, and provides AI-powered corrections
"""

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any, Callable, Dict, List, Optional

import ollama
from ollama import Client
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)


class Correction(BaseModel):
    issue_id: int
    file: str
    line: int
    original: str
    fixed: str


class Issue:
    """Represents a code issue"""

    def __init__(self, issue_id: int, rule_id: int, file: str, line: int):
        self.id = issue_id
        self.rule_id = rule_id
        self.file = file
        self.line = line

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Issue":
        """Create Issue from JSON data"""
        return cls(
            issue_id=data["id"],
            rule_id=data["rule_id"],
            file=data["file"],
            line=data["line"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "file": self.file,
            "line": self.line,
        }


class Rule:
    """Represents a code rule"""

    def __init__(
        self,
        rule_id: int,
        name: str,
        description: str,
        language: str,
        tags: List[str],
        parameters: Dict[str, Any],
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.language = language
        self.tags = tags
        self.parameters = parameters

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Rule":
        """Create Rule from JSON data"""
        return cls(
            rule_id=data["rule_id"],
            name=data["name"],
            description=data["Description"],
            language=data["language"],
            tags=data.get("tags", []),
            parameters=data.get("parameters", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "Description": self.description,
            "language": self.language,
            "tags": self.tags,
            "parameters": self.parameters,
        }


class FileReader:
    """Tool for reading files"""

    def __init__(self, workspace_root: Optional[Path] = None):
        """Initialize file reader

        Args:
            workspace_root: Optional root directory for file access
        """
        self.workspace_root = workspace_root or Path.cwd()

    def read_file(
        self, file_path: str, start_line: int = 1, end_line: Optional[int] = None
    ) -> str:
        """
        Read a file or portion of a file

        Args:
            file_path (str): Path to the file to read
            start_line (int): Starting line number (1-indexed). Defaults to 1.
            end_line (int, optional): Ending line number (inclusive).
                Defaults to None for end of file.

        Returns:
            str: File content as string
        """
        try:
            path = self.workspace_root / file_path

            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # Adjust line numbers (convert to 0-indexed)
            start_idx = max(0, start_line - 1)
            end_idx = end_line if end_line is None else end_line

            # Extract requested lines
            if end_idx is None:
                content_lines = lines[start_idx:]
            else:
                content_lines = lines[start_idx:end_idx]

            content = "".join(content_lines)

            logger.info(
                f"📖 Read file: {file_path} (lines {start_line}-{end_line or 'end'})"
            )
            return content

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise


class IssueCorrector:
    """Manages AI-powered issue corrections with predictable responses"""

    def __init__(
        self, host: str = "http://10.0.0.1:11434", workspace_root: Optional[Path] = None
    ):
        """Initialize issue corrector

        Args:
            host: Ollama server URL
            workspace_root: Optional workspace root directory
        """
        self.client = Client(host=host)
        self.host = host
        self.file_reader = FileReader(workspace_root)

        # Map function names to methods for tool calls
        self.available_functions: Dict[str, Callable] = {
            "read_file": self.file_reader.read_file
        }

    def parse_correction_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response to extract correction

        Args:
            response: Raw AI response

        Returns:
            Parsed correction data

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to parse the entire response as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # Extract JSON object from response
            start_idx = response.find("{")
            if start_idx == -1:
                raise ValueError("No JSON object found in response")

            # Find matching closing brace
            brace_count = 0
            for i in range(start_idx, len(response)):
                if response[i] == "{":
                    brace_count += 1
                elif response[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = response[start_idx : i + 1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON: {e}")
                            raise ValueError(f"Could not parse JSON: {e}")

            raise ValueError("Incomplete JSON object in response")

    def get_correction(
        self, issue: Issue, rule: Rule, model: str = "llama3.1:latest"
    ) -> Dict[str, Any]:
        """Get AI correction for an issue

        Args:
            issue: The issue to correct
            rule: The rule that was violated
            model: Ollama model to use

        Returns:
            Correction data with analysis and fix
        """
        try:
            # Prepare initial message with context about the issue
            messages = [
                {
                    "role": "user",
                    "content": f"""Use the read_file tool to examine {issue.file} around line {issue.line}, then fix this issue:
- Issue id: {issue.id}
- Rule: {rule.name}
- Description: {rule.description}
- Parameters: {json.dumps(rule.parameters)}

IMPORTANT:
- The 'original' field must contain the EXACT line from the file that has the issue
- The 'fixed' field must contain the CORRECTED version that follows the rule
- For this rule, the correction means: {rule.description} with {rule.parameters}""",  # noqa: E501
                }
            ]

            logger.info(
                f"🤖 Requesting correction for issue {issue.id} with rule {rule.rule_id}"
            )

            # Keep trying until the file is read
            file_read = False
            max_attempts = 3
            attempts = 0

            while not file_read and attempts < max_attempts:
                attempts += 1
                logger.info(f"🔄 Attempt {attempts}/{max_attempts} to get tool calls")

                # Get response with tools
                response = self.client.chat(
                    model=model,
                    messages=messages,
                    tools=list(self.available_functions.values()),
                )

                # Process tool calls if any
                if hasattr(response, "message") and hasattr(
                    response.message, "tool_calls"
                ):
                    tool_calls = response.message.tool_calls or []
                    logger.info(f"🔧 Model requested {len(tool_calls)} tool call(s)")

                    logger.debug(f"Response message: {response.message}")

                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = tool_call.function.arguments
                        logger.info(
                            f"📞 Calling tool: {function_name} "
                            f"with args: {function_args}"
                        )

                        if function_name in self.available_functions:
                            try:
                                result = self.available_functions[function_name](
                                    **function_args
                                )
                                logger.info(
                                    f"✅ Tool {function_name} executed successfully"
                                )
                                logger.debug(
                                    f"Tool result preview: {result[:200]}..."
                                    if len(result) > 200
                                    else f"Tool result: {result}"
                                )
                                messages.append({"role": "tool", "content": result})
                                if function_name == "read_file":
                                    file_read = True
                            except Exception as e:
                                logger.error(f"❌ Error executing {function_name}: {e}")
                                messages.append(
                                    {"role": "tool", "content": f"Error: {str(e)}"}
                                )
                        else:
                            logger.warning(
                                f"⚠️ Unknown tool requested: {function_name}"
                            )
                else:
                    logger.warning("⚠️ No tool calls in response")
                    # Add a more explicit message to force tool usage
                    messages.append(
                        {
                            "role": "user",
                            "content": "You MUST use the read_file tool first to see "
                            "the actual content of the file before providing a "
                            "correction. Please use the read_file tool now.",
                        }
                    )

            if not file_read:
                raise ValueError(
                    f"Model failed to read file after {max_attempts} attempts"
                )

            # Get final response after tool use
            logger.info("📝 Getting final response with JSON format")
            response = self.client.chat(
                model=model, messages=messages, format=Correction.model_json_schema()
            )

            # Extract and parse the response
            ai_content = (
                response.message.content
                if hasattr(response, "message")
                else str(response)
            )

            correction_data = self.parse_correction_response(ai_content)

            logger.info(f"✅ Received correction for issue {issue.id}")
            return correction_data

        except ollama.ResponseError as e:
            logger.error(f"Ollama API error: {e.error}")
            raise
        except Exception as e:
            logger.error(f"Error getting correction: {e}")
            raise


class IssueManager:
    """Manages issues and rules from API or files"""

    def __init__(self):
        self.issues: List[Issue] = []
        self.rules: Dict[int, Rule] = {}

    def load_issues_from_json(self, json_data: List[Dict[str, Any]]) -> None:
        """Load issues from JSON data"""
        self.issues = [Issue.from_json(issue_data) for issue_data in json_data]
        logger.info(f"📋 Loaded {len(self.issues)} issues")

    def load_rules_from_json(self, json_data: List[Dict[str, Any]]) -> None:
        """Load rules from JSON data"""
        for rule_data in json_data:
            rule = Rule.from_json(rule_data)
            self.rules[rule.rule_id] = rule
        logger.info(f"📏 Loaded {len(self.rules)} rules")

    def get_rule_for_issue(self, issue: Issue) -> Optional[Rule]:
        """Get the rule associated with an issue"""
        return self.rules.get(issue.rule_id)

    def get_issues_by_file(self, file_path: str) -> List[Issue]:
        """Get all issues for a specific file"""
        return [issue for issue in self.issues if issue.file == file_path]


def process_issues_batch(
    issue_manager: IssueManager,
    corrector: IssueCorrector,
    model: str,
    output_file: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Process all issues and generate corrections

    Args:
        issue_manager: IssueManager with loaded issues and rules
        corrector: IssueCorrector instance
        model: Model to use
        output_file: Optional file to save corrections

    Returns:
        List of corrections
    """
    corrections = []

    for issue in issue_manager.issues:
        rule = issue_manager.get_rule_for_issue(issue)

        if not rule:
            logger.warning(f"⚠️  No rule found for issue {issue.id}")
            continue

        try:
            print(f"\n🔍 Processing issue {issue.id} in {issue.file}:{issue.line}")
            print(f"   Rule: {rule.name}")

            correction = corrector.get_correction(issue, rule, model)

            corrections.append(correction)

            # Display correction
            print(f"   ✅ {correction.get('analysis', 'Correction generated')}")

        except Exception as e:
            logger.error(f"Failed to process issue {issue.id}: {e}")
            corrections.append(
                {"issue": issue.to_dict(), "rule": rule.to_dict(), "error": str(e)}
            )

    # Save corrections if output file specified
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(corrections, f, indent=2)
        print(f"\n💾 Saved corrections to {output_file}")

    return corrections


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="Ollama AI CLI Tool - Issue and Rule Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
              # Process issues from files
              python cli_issues.py --issues issues.json --rules rules.json

              # Process with custom model and save output
              python cli_issues.py --issues issues.json --rules rules.json \\
                  -m codellama --output corrections.json
        """,
    )

    parser.add_argument("--issues", help="JSON file containing issues")
    parser.add_argument("--rules", help="JSON file containing rules")
    parser.add_argument(
        "--host",
        default="http://10.0.0.1:11434",
        help="Ollama server URL (default: http://10.0.0.1:11434)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="llama3.1:latest",
        help="Ollama model to use (default: llama3.1:latest)",
    )
    parser.add_argument("--output", help="Output file for corrections (JSON format)")
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root directory (default: current directory)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    return parser


def main() -> int:
    """Main entry point"""
    parser = _create_argument_parser()
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        # Initialize corrector
        workspace_path = Path(args.workspace).resolve()
        corrector = IssueCorrector(args.host, workspace_path)

        # Batch processing mode
        if not args.issues or not args.rules:
            parser.error("--issues and --rules are required")

        # Load issues and rules
        issue_manager = IssueManager()

        with open(args.issues, "r", encoding="utf-8") as f:
            issues_data = json.load(f)
            issue_manager.load_issues_from_json(issues_data)

        with open(args.rules, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
            issue_manager.load_rules_from_json(rules_data)

        # Process issues
        corrections = process_issues_batch(
            issue_manager, corrector, args.model, args.output
        )

        print(f"\n✅ Processed {len(corrections)} issues")

        return 0

    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
