#!/usr/bin/env python3
"""
Ollama AI CLI Tool - Workspace File Management with Tools
Allows Ollama models to interact with and modify files in a repository
workspace using function calling
"""

import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import shutil
import sys
from typing import Any, Callable, Dict, List, Optional

import ollama
from ollama import Client

# Configure logging
logger = logging.getLogger(__name__)


class WorkspaceManager:
    """Manages file operations within a secure workspace directory"""

    def __init__(self, workspace_root: str):
        """Initialize workspace manager with root directory

        Args:
            workspace_root: Absolute path to the workspace root directory

        Raises:
            ValueError: If workspace root doesn't exist or isn't a directory
        """
        self.workspace_root = Path(workspace_root).resolve()
        if not self.workspace_root.exists():
            raise ValueError(f"Workspace root does not exist: {workspace_root}")
        if not self.workspace_root.is_dir():
            raise ValueError(f"Workspace root is not a directory: {workspace_root}")

        logger.info(f"🗂️  Workspace initialized: {self.workspace_root}")

    def validate_path(self, file_path: str) -> Path:
        """Validate and resolve a file path within the workspace

        Args:
            file_path: Relative or absolute path to validate

        Returns:
            Resolved Path object within workspace

        Raises:
            ValueError: If path is outside workspace
        """
        # Convert to Path and resolve
        path = Path(file_path)
        if path.is_absolute():
            resolved_path = path.resolve()
        else:
            resolved_path = (self.workspace_root / path).resolve()

        # Security check: ensure path is within workspace
        try:
            resolved_path.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError(f"Path outside workspace: {file_path}")

        return resolved_path


class FileTools:
    """File management tools for Ollama function calling"""

    def __init__(self, workspace_manager: WorkspaceManager):
        """Initialize file tools with workspace manager

        Args:
            workspace_manager: WorkspaceManager instance for secure operations
        """
        self.workspace = workspace_manager

    def read_file(self, file_path: str) -> str:
        """
        Read the content of a file in the workspace

        Args:
            file_path: Path to the file relative to workspace root

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If access is denied
        """
        try:
            path = self.workspace.validate_path(file_path)

            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if not path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            logger.info(f"📖 Read file: {file_path} ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    def write_file(self, file_path: str, content: str) -> bool:
        """
        Write content to a file in the workspace

        Args:
            file_path: Path to the file relative to workspace root
            content: Content to write to the file

        Returns:
            True if successful

        Raises:
            PermissionError: If write access is denied
        """
        try:
            path = self.workspace.validate_path(file_path)

            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Decode escape sequences like \n, \t, etc.
            decoded_content = content.encode().decode("unicode_escape")

            with open(path, "w", encoding="utf-8") as f:
                f.write(decoded_content)

            logger.info(f"✏️  Wrote file: {file_path} ({len(decoded_content)} chars)")
            return True

        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            raise

    def list_files(
        self, directory: str = "", pattern: str = "*"
    ) -> List[Dict[str, Any]]:
        """
        List files and directories in the workspace

        Args:
            directory: Directory to list (relative to workspace root, empty for root)
            pattern: Glob pattern to match files (default: "*")

        Returns:
            List of dictionaries containing file information
        """
        try:
            if directory:
                search_dir = self.workspace.validate_path(directory)
            else:
                search_dir = self.workspace.workspace_root

            if not search_dir.exists():
                return []

            files = []
            for path in search_dir.glob(pattern):
                try:
                    relative_path = path.relative_to(self.workspace.workspace_root)
                    if path.is_file():
                        stat = path.stat()
                        files.append(
                            {
                                "name": path.name,
                                "path": str(relative_path),
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(
                                    stat.st_mtime
                                ).isoformat(),
                                "type": "file",
                            }
                        )
                    elif path.is_dir():
                        files.append(
                            {
                                "name": path.name,
                                "path": str(relative_path),
                                "type": "directory",
                            }
                        )
                except (OSError, ValueError):
                    # Skip files we can't access
                    continue

            logger.info(f"📁 Listed {len(files)} items in {directory or 'root'}")
            return sorted(files, key=lambda x: (x["type"], x["name"]))

        except Exception as e:
            logger.error(f"Error listing files in {directory}: {e}")
            raise

    def create_directory(self, dir_path: str) -> bool:
        """
        Create a directory in the workspace

        Args:
            dir_path: Path to the directory relative to workspace root

        Returns:
            True if successful

        Raises:
            PermissionError: If creation is not allowed
        """
        try:
            path = self.workspace.validate_path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created directory: {dir_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            raise

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file or directory in the workspace

        Args:
            file_path: Path to the file/directory relative to workspace root

        Returns:
            True if successful

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If deletion is not allowed
        """
        try:
            path = self.workspace.validate_path(file_path)

            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if path.is_file():
                path.unlink()
                logger.info(f"🗑️  Deleted file: {file_path}")
            elif path.is_dir():
                shutil.rmtree(path)
                logger.info(f"🗑️  Deleted directory: {file_path}")
            else:
                raise ValueError(f"Unknown file type: {file_path}")

            return True

        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")
            raise

    def append_to_file(self, file_path: str, content: str) -> bool:
        """
        Append content to the end of a file

        Args:
            file_path: Path to the file relative to workspace root
            content: Content to append

        Returns:
            True if successful
        """
        try:
            path = self.workspace.validate_path(file_path)

            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Decode escape sequences like \n, \t, etc.
            decoded_content = content.encode().decode("unicode_escape")

            with open(path, "a", encoding="utf-8") as f:
                f.write(decoded_content)

            logger.info(
                f"➕ Appended to file: {file_path} ({len(decoded_content)} chars)"
            )
            return True

        except Exception as e:
            logger.error(f"Error appending to file {file_path}: {e}")
            raise

    def find_files(
        self, name_pattern: str, content_pattern: Optional[str] = None
    ) -> List[str]:
        """
        Find files by name pattern and optionally by content

        Args:
            name_pattern: Glob pattern for file names
            content_pattern: Optional string to search within file contents

        Returns:
            List of relative file paths that match the criteria
        """
        try:
            matching_files = []

            for path in self.workspace.workspace_root.rglob(name_pattern):
                if path.is_file():
                    relative_path = str(path.relative_to(self.workspace.workspace_root))

                    if self._should_include_file(path, content_pattern):
                        matching_files.append(relative_path)

            logger.info(
                f"🔍 Found {len(matching_files)} files matching '{name_pattern}'"
            )
            return matching_files

        except Exception as e:
            logger.error(f"Error finding files: {e}")
            raise

    def _should_include_file(self, path: Path, content_pattern: Optional[str]) -> bool:
        """Check if file should be included based on content pattern"""
        if not content_pattern:
            return True

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return content_pattern.lower() in f.read().lower()
        except (OSError, UnicodeDecodeError):
            return False

    def get_workspace_info(self) -> Dict[str, Any]:
        """
        Get information about the workspace

        Returns:
            Dictionary containing workspace statistics and information
        """
        try:
            total_files = 0
            total_size = 0
            file_types: Dict[str, int] = {}

            for path in self.workspace.workspace_root.rglob("*"):
                if path.is_file():
                    total_files += 1
                    try:
                        size = path.stat().st_size
                        total_size += size

                        # Count file types by extension
                        ext = path.suffix.lower() or "no_extension"
                        file_types[ext] = file_types.get(ext, 0) + 1
                    except OSError:
                        continue

            return {
                "root": str(self.workspace.workspace_root),
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "is_git_repo": (self.workspace.workspace_root / ".git").exists(),
                "exists": self.workspace.workspace_root.exists(),
            }

        except Exception as e:
            logger.error(f"Error getting workspace info: {e}")
            raise


class WorkspaceChat:
    """Manages conversations with Ollama using file management tools"""

    def __init__(self, workspace_root: str, host: str = "http://10.0.0.1:11434"):
        """Initialize workspace chat manager

        Args:
            workspace_root: Path to workspace directory
            host: Ollama server URL
        """
        self.workspace_manager = WorkspaceManager(workspace_root)
        self.file_tools = FileTools(self.workspace_manager)
        self.client = Client(host=host)
        self.host = host

        # Map function names to methods for tool call processing
        self.available_functions: Dict[str, Callable] = {
            "read_file": self.file_tools.read_file,
            "write_file": self.file_tools.write_file,
            "list_files": self.file_tools.list_files,
            "create_directory": self.file_tools.create_directory,
            "delete_file": self.file_tools.delete_file,
            "append_to_file": self.file_tools.append_to_file,
            "find_files": self.file_tools.find_files,
            "get_workspace_info": self.file_tools.get_workspace_info,
        }

    def get_system_prompt(self) -> str:
        """Create system prompt describing available tools"""
        return f"""You are an AI assistant with access to file management tools in a \
secure workspace.

Workspace root: {self.workspace_manager.workspace_root}

Available tools:
- read_file(file_path): Read content of a file
- write_file(file_path, content): Create or overwrite a file with content
- list_files(directory="", pattern="*"): List files and directories
- create_directory(dir_path): Create a directory
- delete_file(file_path): Delete a file or directory
- append_to_file(file_path, content): Append content to a file
- find_files(name_pattern, content_pattern=None): Find files by name/content
- get_workspace_info(): Get workspace statistics

Guidelines:
- All file paths are relative to the workspace root
- You can only operate within the assigned workspace
- Always explain what you're doing before making changes
- Be careful with destructive operations (delete, overwrite)
- Use list_files() to explore the workspace structure first
- Provide clear feedback about operations performed

When modifying files, describe your actions clearly and confirm successful \
operations."""

    def chat_interactive(
        self, model: str, initial_prompt: str, max_iterations: int = 10
    ) -> None:
        """Start an interactive chat session with file tools

        Args:
            model: Ollama model name
            initial_prompt: Initial user request
            max_iterations: Maximum conversation rounds
        """
        try:
            messages = self._initialize_chat(initial_prompt)
            self._print_chat_header(initial_prompt)

            for _ in range(max_iterations):
                response = self._get_ai_response(model, messages)

                if not hasattr(response, "message"):
                    print("❌ Invalid response from AI")
                    break

                message = response.message
                ai_content = message.content or ""

                if ai_content:
                    print(f"🤖 AI: {ai_content}")

                # Process tool calls and update messages
                self._process_tool_calls(message, messages)

                # Add AI response to conversation
                messages.append({"role": "assistant", "content": ai_content})

                # Get next user input
                if not self._get_user_input(messages):
                    break

            print("💬 Conversation ended")

        except ollama.ResponseError as e:
            self._handle_ollama_error(e)
        except Exception as e:
            logger.error(f"Error in chat session: {e}")

    def _initialize_chat(self, initial_prompt: str) -> List[Dict[str, str]]:
        """Initialize chat messages"""
        return [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": initial_prompt},
        ]

    def _print_chat_header(self, initial_prompt: str) -> None:
        """Print chat session header"""
        print(
            f"🤖 AI Assistant ready with workspace: "
            f"{self.workspace_manager.workspace_root}"
        )
        print(f"📝 Initial request: {initial_prompt}")
        print("=" * 80)

    def _get_ai_response(self, model: str, messages: List[Dict[str, str]]) -> Any:
        """Get response from AI model"""
        tools_functions = list(self.available_functions.values())

        if logger.level <= logging.DEBUG:
            logger.debug(f"Sending {len(tools_functions)} tools to model")
            logger.debug(f"Tools: {list(self.available_functions.keys())}")

        response = self.client.chat(
            model=model, messages=messages, tools=tools_functions
        )

        if logger.level <= logging.DEBUG:
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response: {response}")

        return response

    def _process_tool_calls(self, message: Any, messages: List[Dict[str, str]]) -> None:
        """Process tool calls from AI response"""
        tool_calls = getattr(message, "tool_calls", None) or []
        if not tool_calls:
            return

        print(f"🔧 AI is using {len(tool_calls)} tool(s)...")

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments

            if function_name in self.available_functions:
                self._execute_tool_call(function_name, function_args, messages)
            else:
                print(f"  ❌ Unknown function: {function_name}")

    def _execute_tool_call(
        self,
        function_name: str,
        function_args: Dict[str, Any],
        messages: List[Dict[str, str]],
    ) -> None:
        """Execute a single tool call"""
        try:
            args_str = ", ".join(f"{k}={repr(v)}" for k, v in function_args.items())
            print(f"  📋 Calling {function_name}({args_str})")
            result = self.available_functions[function_name](**function_args)
            print(f"  ✅ Result: {result}")

            # Add tool result to conversation
            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result)
                    if not isinstance(result, str)
                    else result,
                }
            )

        except Exception as e:
            error_msg = f"Error executing {function_name}: {e}"
            print(f"  ❌ {error_msg}")
            messages.append({"role": "tool", "content": error_msg})

    def _get_user_input(self, messages: List[Dict[str, str]]) -> bool:
        """Get user input and return True if chat should continue"""
        print()
        user_input = input("👤 You: ").strip()
        if user_input.lower() in ["exit", "quit", "done", ""]:
            return False

        messages.append({"role": "user", "content": user_input})
        print()
        return True

    def _handle_ollama_error(self, error: ollama.ResponseError) -> None:
        """Handle Ollama API errors"""
        logger.error(f"Ollama API error: {error.error}")
        if error.status_code == 404:
            logger.error("Model not found. Try: ollama pull <model>")


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="Ollama AI CLI Tool - Workspace File Management with Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_workspace.py /path/to/repo "Create a new README.md file"
  python cli_workspace.py . "List all Python files and show their content"
  python cli_workspace.py /workspace "Refactor the main.py file"
        """,
    )

    parser.add_argument(
        "workspace", help="Path to the workspace directory (repository root)"
    )
    parser.add_argument("prompt", help="Initial prompt/request for the AI")
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
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum number of conversation rounds (default: 10)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    return parser


def main() -> int:
    """Main entry point for the CLI application"""
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
        # Validate workspace
        workspace_path = Path(args.workspace).resolve()
        if not workspace_path.exists():
            logger.error(f"Workspace directory does not exist: {args.workspace}")
            return 1

        if not workspace_path.is_dir():
            logger.error(f"Workspace path is not a directory: {args.workspace}")
            return 1

        # Start interactive session
        chat = WorkspaceChat(str(workspace_path), args.host)
        chat.chat_interactive(args.model, args.prompt, args.max_iterations)

        return 0

    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
