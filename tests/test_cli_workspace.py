"""
Tests for cli_workspace.py functionality
"""

import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_workspace import FileTools, WorkspaceChat, WorkspaceManager  # noqa: E402


class TestWorkspaceManager:
    """Test workspace management functionality"""

    def test_init_valid_workspace(self, temp_dir: str) -> None:
        """Test initialization with valid workspace"""
        manager = WorkspaceManager(temp_dir)
        assert manager.workspace_root == Path(temp_dir).resolve()

    def test_init_nonexistent_workspace(self) -> None:
        """Test initialization with non-existent directory"""
        with pytest.raises(ValueError, match="Workspace root does not exist"):
            WorkspaceManager("/nonexistent/path")

    def test_init_file_as_workspace(self, temp_file: str) -> None:
        """Test initialization with file instead of directory"""
        with pytest.raises(ValueError, match="Workspace root is not a directory"):
            WorkspaceManager(temp_file)

    def test_validate_path_relative(self, temp_dir: str) -> None:
        """Test path validation with relative path"""
        manager = WorkspaceManager(temp_dir)
        validated = manager.validate_path("subdir/file.txt")
        assert validated == Path(temp_dir).resolve() / "subdir" / "file.txt"

    def test_validate_path_absolute_inside(self, temp_dir: str) -> None:
        """Test path validation with absolute path inside workspace"""
        manager = WorkspaceManager(temp_dir)
        file_path = os.path.join(temp_dir, "file.txt")
        validated = manager.validate_path(file_path)
        assert validated == Path(file_path).resolve()

    def test_validate_path_outside_workspace(self, temp_dir: str) -> None:
        """Test path validation with path outside workspace"""
        manager = WorkspaceManager(temp_dir)
        with pytest.raises(ValueError, match="Path outside workspace"):
            manager.validate_path("../outside.txt")

    def test_validate_path_traversal_attempt(self, temp_dir: str) -> None:
        """Test path validation with directory traversal attempt"""
        manager = WorkspaceManager(temp_dir)
        with pytest.raises(ValueError, match="Path outside workspace"):
            manager.validate_path("subdir/../../outside.txt")


class TestFileTools:
    """Test file manipulation tools"""

    def test_read_file_success(self, temp_dir: str) -> None:
        """Test successful file reading"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        # Read file
        content = tools.read_file("test.txt")
        assert content == test_content

    def test_read_file_not_found(self, temp_dir: str) -> None:
        """Test reading non-existent file"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        with pytest.raises(FileNotFoundError):
            tools.read_file("nonexistent.txt")

    def test_read_file_directory(self, temp_dir: str) -> None:
        """Test reading a directory instead of file"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create subdirectory
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()

        with pytest.raises(ValueError, match="Path is not a file"):
            tools.read_file("subdir")

    def test_write_file_success(self, temp_dir: str) -> None:
        """Test successful file writing"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        content = "New content"
        result = tools.write_file("new_file.txt", content)

        assert result is True
        assert (Path(temp_dir) / "new_file.txt").read_text() == content

    def test_write_file_with_subdirs(self, temp_dir: str) -> None:
        """Test writing file with creating subdirectories"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        content = "Nested content"
        result = tools.write_file("sub/dir/file.txt", content)

        assert result is True
        assert (Path(temp_dir) / "sub" / "dir" / "file.txt").read_text() == content

    def test_list_files_root(self, temp_dir: str) -> None:
        """Test listing files in root directory"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create test files
        (Path(temp_dir) / "file1.txt").write_text("content1")
        (Path(temp_dir) / "file2.py").write_text("content2")
        (Path(temp_dir) / "subdir").mkdir()

        files = tools.list_files()

        assert len(files) == 3
        file_names = [f["name"] for f in files]
        assert "file1.txt" in file_names
        assert "file2.py" in file_names
        assert "subdir" in file_names

    def test_list_files_with_pattern(self, temp_dir: str) -> None:
        """Test listing files with glob pattern"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create test files
        (Path(temp_dir) / "test1.py").write_text("content1")
        (Path(temp_dir) / "test2.py").write_text("content2")
        (Path(temp_dir) / "other.txt").write_text("content3")

        files = tools.list_files("", "*.py")

        assert len(files) == 2
        assert all(f["name"].endswith(".py") for f in files)

    def test_create_directory(self, temp_dir: str) -> None:
        """Test directory creation"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        result = tools.create_directory("new_dir/sub_dir")

        assert result is True
        assert (Path(temp_dir) / "new_dir" / "sub_dir").is_dir()

    def test_delete_file(self, temp_dir: str) -> None:
        """Test file deletion"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create and delete file
        test_file = Path(temp_dir) / "to_delete.txt"
        test_file.write_text("delete me")

        result = tools.delete_file("to_delete.txt")

        assert result is True
        assert not test_file.exists()

    def test_delete_directory(self, temp_dir: str) -> None:
        """Test directory deletion"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create directory with content
        dir_path = Path(temp_dir) / "to_delete"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content")

        result = tools.delete_file("to_delete")

        assert result is True
        assert not dir_path.exists()

    def test_append_to_file(self, temp_dir: str) -> None:
        """Test appending to file"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create initial file
        test_file = Path(temp_dir) / "append.txt"
        test_file.write_text("Initial content\n")

        # Append
        result = tools.append_to_file("append.txt", "Appended content")

        assert result is True
        assert test_file.read_text() == "Initial content\nAppended content"

    def test_find_files_by_name(self, temp_dir: str) -> None:
        """Test finding files by name pattern"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create test files
        (Path(temp_dir) / "test1.py").write_text("content")
        (Path(temp_dir) / "subdir").mkdir()
        (Path(temp_dir) / "subdir" / "test2.py").write_text("content")
        (Path(temp_dir) / "other.txt").write_text("content")

        files = tools.find_files("*.py")

        assert len(files) == 2
        assert "test1.py" in files
        assert "subdir/test2.py" in files

    def test_find_files_by_content(self, temp_dir: str) -> None:
        """Test finding files by content pattern"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create test files with different content
        (Path(temp_dir) / "file1.txt").write_text("Hello World")
        (Path(temp_dir) / "file2.txt").write_text("Goodbye World")
        (Path(temp_dir) / "file3.txt").write_text("Hello Python")

        files = tools.find_files("*.txt", "Hello")

        assert len(files) == 2
        assert "file1.txt" in files
        assert "file3.txt" in files

    def test_get_workspace_info(self, temp_dir: str) -> None:
        """Test getting workspace information"""
        manager = WorkspaceManager(temp_dir)
        tools = FileTools(manager)

        # Create test files
        (Path(temp_dir) / "file1.py").write_text("x" * 100)
        (Path(temp_dir) / "file2.txt").write_text("x" * 200)

        info = tools.get_workspace_info()

        assert info["root"] == str(Path(temp_dir).resolve())
        assert info["total_files"] == 2
        assert info["total_size"] == 300
        assert ".py" in info["file_types"]
        assert ".txt" in info["file_types"]
        assert info["exists"] is True


class TestWorkspaceChat:
    """Test workspace chat functionality"""

    def test_init(self, temp_dir: str) -> None:
        """Test WorkspaceChat initialization"""
        chat = WorkspaceChat(temp_dir)
        assert chat.workspace_manager.workspace_root == Path(temp_dir).resolve()
        assert len(chat.available_functions) == 8

    def test_get_system_prompt(self, temp_dir: str) -> None:
        """Test system prompt generation"""
        chat = WorkspaceChat(temp_dir)
        prompt = chat.get_system_prompt()

        assert str(Path(temp_dir).resolve()) in prompt
        assert "read_file" in prompt
        assert "write_file" in prompt
        assert "list_files" in prompt

    @patch("cli_workspace.Client")
    def test_chat_interactive_tool_call(
        self, mock_client_class: Mock, temp_dir: str
    ) -> None:
        """Test interactive chat with tool call"""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock response with tool call
        mock_response = {
            "message": {
                "content": "I'll read the file for you.",
                "tool_calls": [
                    {
                        "function": {
                            "name": "read_file",
                            "arguments": {"file_path": "test.txt"},
                        }
                    }
                ],
            }
        }

        mock_client.chat.return_value = mock_response

        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Test content")

        # Test chat
        chat = WorkspaceChat(temp_dir)

        # Mock user input to exit after first iteration
        with patch("builtins.input", return_value="exit"):
            chat.chat_interactive("llama3.1", "Read test.txt", max_iterations=1)

        # Verify chat was called
        mock_client.chat.assert_called_once()
        call_args = mock_client.chat.call_args
        assert call_args[1]["model"] == "llama3.1"
        assert len(call_args[1]["tools"]) == 8

    @patch("cli_workspace.Client")
    def test_chat_interactive_error_handling(
        self, mock_client_class: Mock, temp_dir: str
    ) -> None:
        """Test error handling in interactive chat"""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock response with tool call for non-existent file
        mock_response = {
            "message": {
                "content": "I'll read the file.",
                "tool_calls": [
                    {
                        "function": {
                            "name": "read_file",
                            "arguments": {"file_path": "nonexistent.txt"},
                        }
                    }
                ],
            }
        }

        mock_client.chat.return_value = mock_response

        # Test chat
        chat = WorkspaceChat(temp_dir)

        # Mock user input to exit after first iteration
        with patch("builtins.input", return_value="exit"):
            chat.chat_interactive("llama3.1", "Read nonexistent.txt", max_iterations=1)

        # Chat should handle the error gracefully
        mock_client.chat.assert_called_once()


class TestCLIIntegration:
    """Test CLI integration"""

    def test_main_nonexistent_workspace(self) -> None:
        """Test main with non-existent workspace"""
        from cli_workspace import main

        with patch("sys.argv", ["cli_workspace.py", "/nonexistent", "test"]):
            result = main()
            assert result == 1

    def test_main_file_as_workspace(self, temp_file: str) -> None:
        """Test main with file instead of directory"""
        from cli_workspace import main

        with patch("sys.argv", ["cli_workspace.py", temp_file, "test"]):
            result = main()
            assert result == 1

    @patch("cli_workspace.WorkspaceChat")
    def test_main_success(self, mock_chat_class: Mock, temp_dir: str) -> None:
        """Test successful main execution"""
        from cli_workspace import main

        # Setup mock
        mock_chat = Mock()
        mock_chat_class.return_value = mock_chat

        with patch("sys.argv", ["cli_workspace.py", temp_dir, "List files"]):
            result = main()
            assert result == 0

        # Verify chat was initialized and called
        mock_chat_class.assert_called_once()
        mock_chat.chat_interactive.assert_called_once_with(
            "llama3.1:latest", "List files", 10
        )
