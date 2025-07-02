"""
Tests for cli_file.py functionality
"""

import logging
import os
import sys
import tempfile
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_file import (  # noqa: E402
    _configure_logging,
    _create_argument_parser,
    _expand_file_patterns,
    _process_multiple_files,
    _process_single_file,
    _validate_files,
    analyze_file_with_ollama_async,
    analyze_file_with_ollama_sync,
    check_empty_catch_blocks,
    check_hardcoded_credentials,
    check_long_lines,
    check_print_statements,
    check_todo_comments,
    check_unused_imports,
    generate_output_filename,
    get_static_analysis_issues,
    process_multiple_files_async,
    read_file_content,
    save_to_markdown,
)


class TestStaticAnalysis:
    """Test static analysis functionality"""

    def test_get_static_analysis_issues_with_todo(self, temp_file: str) -> None:
        """Test detection of TODO comments"""
        issues = get_static_analysis_issues(temp_file)

        # Should find TODO comment
        todo_issues = [i for i in issues if "TODO" in i["message"]]
        assert len(todo_issues) > 0
        assert todo_issues[0]["type"] == "code_smell"
        assert todo_issues[0]["severity"] == "INFO"

    def test_get_static_analysis_issues_with_print(self, temp_file: str) -> None:
        """Test detection of print statements"""
        issues = get_static_analysis_issues(temp_file)

        # Should find print statement
        print_issues = [i for i in issues if "print(" in i["code"]]
        assert len(print_issues) > 0
        assert print_issues[0]["type"] == "code_smell"
        assert print_issues[0]["severity"] == "MINOR"

    def test_get_static_analysis_issues_with_credentials(self, temp_file: str) -> None:
        """Test detection of hardcoded credentials"""
        issues = get_static_analysis_issues(temp_file)

        # Should find hardcoded credential
        cred_issues = [i for i in issues if "credential" in i["message"]]
        assert len(cred_issues) > 0
        assert cred_issues[0]["type"] == "vulnerability"
        assert cred_issues[0]["severity"] == "BLOCKER"

    def test_get_static_analysis_issues_with_empty_catch(self, temp_file: str) -> None:
        """Test detection of empty catch blocks"""
        issues = get_static_analysis_issues(temp_file)

        # Should find empty catch block
        catch_issues = [i for i in issues if "exception" in i["message"].lower()]
        assert len(catch_issues) > 0
        assert catch_issues[0]["type"] == "bug"
        assert catch_issues[0]["severity"] == "MAJOR"

    def test_get_static_analysis_issues_no_file(self) -> None:
        """Test with non-existent file"""
        issues = get_static_analysis_issues("non_existent_file.py")
        assert issues == []

    def test_get_static_analysis_issues_clean_file(self) -> None:
        """Test with a clean file (no issues)"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """#!/usr/bin/env python3
def clean_function():
    return "This is clean code"

if __name__ == "__main__":
    result = clean_function()
"""
            )
            temp_path = f.name

        try:
            issues = get_static_analysis_issues(temp_path)
            # Should only find print statements if any, but this file is clean
            assert len(issues) == 0 or all(
                issue["severity"] != "BLOCKER" for issue in issues
            )
        finally:
            os.unlink(temp_path)


class TestFileOperations:
    """Test file reading and writing operations"""

    def test_read_file_content_success(self, temp_file: str) -> None:
        """Test successful file reading"""
        content = read_file_content(temp_file)
        assert content is not None
        assert "def test_function():" in content

    def test_read_file_content_not_found(self) -> None:
        """Test reading non-existent file"""
        content = read_file_content("non_existent_file.py")
        assert content is None

    @patch("builtins.open", side_effect=PermissionError())
    def test_read_file_content_permission_error(self, mock_file: Mock) -> None:
        """Test reading file with permission error"""
        content = read_file_content("restricted_file.py")
        assert content is None

    @patch("builtins.open", side_effect=OSError("Disk full"))
    def test_read_file_content_generic_error(self, mock_file: Mock) -> None:
        """Test reading file with generic exception"""
        content = read_file_content("problematic_file.py")
        assert content is None

    def test_generate_output_filename(self) -> None:
        """Test output filename generation"""
        input_file = "test_script.py"
        output_file = generate_output_filename(input_file)

        # Should contain base name and timestamp
        assert "test_script_analysis_" in output_file
        assert output_file.endswith(".md")

        # Should contain valid timestamp format
        timestamp_part = output_file.replace("test_script_analysis_", "").replace(
            ".md", ""
        )
        assert len(timestamp_part.split("-")) == 2  # date-time format

    def test_save_to_markdown_basic(self, temp_dir: str) -> None:
        """Test basic markdown saving"""
        content = "# Test Analysis\n\nThis is test content."
        filename = "test_output.md"
        analyzed_file = "test.py"

        save_to_markdown(filename, content, analyzed_file, temp_dir)

        output_path = os.path.join(temp_dir, filename)
        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            saved_content = f.read()
            assert f"Analysis Report for {analyzed_file}" in saved_content
            assert content in saved_content

    def test_save_to_markdown_no_output_dir(self, temp_dir: str) -> None:
        """Test markdown saving without output directory"""
        content = "# Test Analysis\n\nThis is test content."
        filename = os.path.join(temp_dir, "test_output.md")
        analyzed_file = "test.py"

        save_to_markdown(filename, content, analyzed_file)

        assert os.path.exists(filename)

    @patch("os.makedirs", side_effect=Exception("Permission denied"))
    def test_save_to_markdown_error(self, mock_makedirs: Mock) -> None:
        """Test markdown saving with error"""
        content = "# Test Analysis"
        filename = "test_output.md"
        analyzed_file = "test.py"

        # Should not raise exception, just print error
        save_to_markdown(filename, content, analyzed_file, "/nonexistent/path")


class TestOllamaIntegration:
    """Test Ollama integration (with mocks)"""

    @patch("cli_file.Client")
    def test_analyze_file_with_ollama_sync_non_streaming(
        self,
        mock_client_class: Mock,
        temp_file: str,
        sample_static_issues: List[Dict[str, Any]],
    ) -> None:
        """Test synchronous Ollama analysis without streaming"""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.return_value = {
            "message": {"content": "Mock analysis response"}
        }
        mock_client_class.return_value = mock_client

        # Read file content
        content = read_file_content(temp_file)

        # Test function
        response = analyze_file_with_ollama_sync(
            host="http://localhost:11434",
            model="mistral:latest",
            file_path=temp_file,
            content=content,
            is_streaming=False,
            sonar_issues=sample_static_issues,
            save_to_file=False,
        )

        assert response == "Mock analysis response"
        mock_client.chat.assert_called_once()

    @patch("cli_file.Client")
    def test_analyze_file_with_ollama_sync_streaming(
        self,
        mock_client_class: Mock,
        temp_file: str,
        sample_static_issues: List[Dict[str, Any]],
        mock_streaming_response: List[Dict[str, Any]],
    ) -> None:
        """Test synchronous Ollama analysis with streaming"""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.return_value = mock_streaming_response
        mock_client_class.return_value = mock_client

        # Read file content
        content = read_file_content(temp_file)

        # Test function
        response = analyze_file_with_ollama_sync(
            host="http://localhost:11434",
            model="mistral:latest",
            file_path=temp_file,
            content=content,
            is_streaming=True,
            sonar_issues=sample_static_issues,
            save_to_file=False,
        )

        assert response == "Mock streaming response"
        mock_client.chat.assert_called_once()

    @pytest.mark.asyncio
    @patch("cli_file.AsyncClient")
    async def test_analyze_file_with_ollama_async_non_streaming(
        self,
        mock_client_class: Mock,
        temp_file: str,
        sample_static_issues: List[Dict[str, Any]],
    ) -> None:
        """Test asynchronous Ollama analysis without streaming"""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.chat.return_value = {
            "message": {"content": "Mock async analysis response"}
        }
        mock_client_class.return_value = mock_client

        # Read file content
        content = read_file_content(temp_file)

        # Test function
        response = await analyze_file_with_ollama_async(
            host="http://localhost:11434",
            model="mistral:latest",
            file_path=temp_file,
            content=content,
            is_streaming=False,
            sonar_issues=sample_static_issues,
            save_to_file=False,
        )

        assert response == "Mock async analysis response"
        mock_client.chat.assert_called_once()

    @patch("cli_file.Client")
    def test_analyze_file_with_ollama_sync_connection_error(
        self,
        mock_client_class: Mock,
        temp_file: str,
        sample_static_issues: List[Dict[str, Any]],
    ) -> None:
        """Test Ollama connection error handling"""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_client.chat.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client

        # Read file content
        content = read_file_content(temp_file)

        # Test function
        response = analyze_file_with_ollama_sync(
            host="http://localhost:11434",
            model="mistral:latest",
            file_path=temp_file,
            content=content,
            is_streaming=False,
            sonar_issues=sample_static_issues,
            save_to_file=False,
        )

        assert response is None


class TestCheckerFunctions:
    """Test individual checker functions for static analysis"""

    def test_check_todo_comments_found(self) -> None:
        """Test TODO comment detection"""
        result = check_todo_comments("# TODO: Fix this later", 5)
        assert result is not None
        assert result["line"] == 5
        assert result["type"] == "code_smell"
        assert result["severity"] == "INFO"
        assert "TODO" in result["message"]

    def test_check_todo_comments_not_found(self) -> None:
        """Test when no TODO comments"""
        result = check_todo_comments("# Regular comment", 1)
        assert result is None

    def test_check_print_statements_python(self) -> None:
        """Test print statement detection in Python files"""
        result = check_print_statements("print('Hello world')", 10, "test.py")
        assert result is not None
        assert result["line"] == 10
        assert result["type"] == "code_smell"
        assert result["severity"] == "MINOR"

    def test_check_print_statements_non_python(self) -> None:
        """Test print statement ignored in non-Python files"""
        result = check_print_statements("print('Hello')", 1, "test.js")
        assert result is None

    def test_check_long_lines(self) -> None:
        """Test long line detection"""
        long_line = "x" * 150  # Create a line longer than 120 chars
        result = check_long_lines(long_line, 3)
        assert result is not None
        assert result["line"] == 3
        assert result["type"] == "code_smell"
        assert result["severity"] == "MINOR"
        assert "120 characters" in result["message"]

    def test_check_long_lines_ok(self) -> None:
        """Test short line passes"""
        result = check_long_lines("short line", 1)
        assert result is None

    def test_check_hardcoded_credentials(self) -> None:
        """Test hardcoded credential detection"""
        result = check_hardcoded_credentials("password='secret123'", 8)
        assert result is not None
        assert result["line"] == 8
        assert result["type"] == "vulnerability"
        assert result["severity"] == "BLOCKER"

    def test_check_hardcoded_credentials_comment(self) -> None:
        """Test credentials in comments are ignored"""
        result = check_hardcoded_credentials("# password='example'", 1)
        assert result is None

    def test_check_unused_imports(self) -> None:
        """Test unused import detection"""
        content = "import json\nprint('hello')"  # json not used
        result = check_unused_imports("import json", 1, content, "test.py")
        assert result is not None
        assert result["type"] == "code_smell"
        assert result["severity"] == "MINOR"
        assert "json" in result["message"]

    def test_check_unused_imports_malformed(self) -> None:
        """Test unused import detection with malformed import line"""
        content = "print('hello')"
        result = check_unused_imports(
            "import", 1, content, "test.py"
        )  # Malformed import
        assert result is None  # Should handle IndexError gracefully


class TestMainHelperFunctions:
    """Test the new helper functions from main() refactoring"""

    def test_create_argument_parser(self) -> None:
        """Test argument parser creation"""
        parser = _create_argument_parser()

        # Test default values
        args = parser.parse_args(["test.py"])
        assert args.host == "http://10.0.0.1:11434"
        assert args.model == "mistral:latest"
        assert args.file == ["test.py"]
        assert args.stream is False
        assert args.verbose is False
        assert args.output is False
        assert args.concurrent == 4

    def test_create_argument_parser_with_options(self) -> None:
        """Test argument parser with all options"""
        parser = _create_argument_parser()

        args = parser.parse_args(
            [
                "file1.py",
                "file2.py",
                "--host",
                "http://localhost:11434",
                "--model",
                "llama3:8b",
                "--stream",
                "--verbose",
                "--output",
                "--concurrent",
                "8",
            ]
        )

        assert args.host == "http://localhost:11434"
        assert args.model == "llama3:8b"
        assert args.file == ["file1.py", "file2.py"]
        assert args.stream is True
        assert args.verbose is True
        assert args.output is True
        assert args.concurrent == 8

    @patch("cli_file.logging.basicConfig")
    def test_configure_logging_verbose(self, mock_basic_config: Mock) -> None:
        """Test logging configuration in verbose mode"""
        _configure_logging(True)
        mock_basic_config.assert_called_once()

        call_args = mock_basic_config.call_args[1]
        assert call_args["level"] == logging.DEBUG
        assert "[%(asctime)s]" in call_args["format"]

    @patch("cli_file.logging.basicConfig")
    def test_configure_logging_quiet(self, mock_basic_config: Mock) -> None:
        """Test logging configuration in quiet mode"""
        _configure_logging(False)
        mock_basic_config.assert_called_once()

        call_args = mock_basic_config.call_args[1]
        assert call_args["level"] == logging.WARNING

    @patch("glob.glob")
    def test_expand_file_patterns_with_glob(self, mock_glob: Mock) -> None:
        """Test file pattern expansion with glob matches"""
        mock_glob.return_value = ["file1.py", "file2.py"]

        result = _expand_file_patterns(["src/*.py"])

        mock_glob.assert_called_once_with("src/*.py")
        assert result == ["file1.py", "file2.py"]

    @patch("glob.glob")
    def test_expand_file_patterns_no_glob(self, mock_glob: Mock) -> None:
        """Test file pattern expansion without glob matches"""
        mock_glob.return_value = []

        result = _expand_file_patterns(["specific_file.py"])

        assert result == ["specific_file.py"]

    @patch("glob.glob")
    def test_expand_file_patterns_deduplication(self, mock_glob: Mock) -> None:
        """Test file pattern deduplication"""
        mock_glob.side_effect = [["file1.py"], ["file1.py", "file2.py"]]

        result = _expand_file_patterns(["pattern1", "pattern2"])

        # Should deduplicate file1.py
        assert result == ["file1.py", "file2.py"]

    def test_validate_files_all_valid(self) -> None:
        """Test file validation with all valid files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = os.path.join(temp_dir, "file1.py")
            file2 = os.path.join(temp_dir, "file2.py")

            # Create test files
            for f in [file1, file2]:
                with open(f, "w") as fd:
                    fd.write("# test")

            result = _validate_files([file1, file2])
            assert len(result) == 2
            assert file1 in result
            assert file2 in result

    def test_validate_files_some_invalid(self) -> None:
        """Test file validation with some invalid files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_file = os.path.join(temp_dir, "valid.py")
            invalid_file = os.path.join(temp_dir, "nonexistent.py")

            # Create only one file
            with open(valid_file, "w") as f:
                f.write("# test")

            result = _validate_files([valid_file, invalid_file])
            assert len(result) == 1
            assert result[0] == valid_file

    def test_validate_files_none_valid(self) -> None:
        """Test file validation with no valid files"""
        result = _validate_files(["nonexistent1.py", "nonexistent2.py"])
        assert result is None

    @patch("cli_file.asyncio.run")
    @patch("cli_file.process_multiple_files_async")
    def test_process_multiple_files(
        self, mock_process_async: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test multiple files processing"""
        mock_args = Mock()
        mock_args.host = "http://localhost:11434"
        mock_args.model = "test-model"
        mock_args.output = False
        mock_args.concurrent = 4
        mock_args.output_dir = None
        mock_args.stream = False

        files = ["file1.py", "file2.py"]

        result = _process_multiple_files(mock_args, files)

        assert result == 0
        mock_asyncio_run.assert_called_once()

    @patch("cli_file.read_file_content")
    @patch("cli_file.get_static_analysis_issues")
    @patch("cli_file.analyze_file_with_ollama_sync")
    def test_process_single_file_with_issues(
        self, mock_analyze: Mock, mock_get_issues: Mock, mock_read_content: Mock
    ) -> None:
        """Test single file processing with issues found"""
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.stream = False
        mock_args.output = False
        mock_args.host = "http://localhost:11434"
        mock_args.model = "test-model"
        mock_args.output_dir = None

        mock_read_content.return_value = "print('test')"
        mock_get_issues.return_value = [{"line": 1, "message": "test issue"}]
        mock_analyze.return_value = "Analysis result"

        result = _process_single_file(mock_args, "test.py")

        assert result == 0
        mock_read_content.assert_called_once_with("test.py")
        mock_get_issues.assert_called_once_with("test.py")
        mock_analyze.assert_called_once()

    @patch("cli_file.read_file_content")
    @patch("cli_file.get_static_analysis_issues")
    @pytest.mark.filterwarnings("ignore:coroutine.*was never awaited:RuntimeWarning")
    def test_process_single_file_no_issues(
        self, mock_get_issues: Mock, mock_read_content: Mock
    ) -> None:
        """Test single file processing with no issues"""
        mock_args = Mock()
        mock_read_content.return_value = "# clean code"
        mock_get_issues.return_value = []  # No issues

        result = _process_single_file(mock_args, "test.py")

        assert result == 0
        mock_read_content.assert_called_once_with("test.py")
        mock_get_issues.assert_called_once_with("test.py")

    @patch("cli_file.read_file_content")
    def test_process_single_file_read_error(self, mock_read_content: Mock) -> None:
        """Test single file processing with read error"""
        mock_args = Mock()
        mock_read_content.return_value = None  # Read error

        result = _process_single_file(mock_args, "test.py")

        assert result == 1


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_file_filtering_integration(self) -> None:
        """Test complete file filtering workflow"""
        # Create some test files
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_file = os.path.join(temp_dir, "valid.py")
            with open(valid_file, "w") as f:
                f.write("# Valid file")

            all_files = [valid_file, "nonexistent.py"]
            valid_files = [
                f for f in all_files if os.path.exists(f) and os.path.isfile(f)
            ]

            assert len(valid_files) == 1
            assert valid_files[0] == valid_file

    @patch("cli_file.analyze_file_with_ollama_sync")
    @patch("cli_file.get_static_analysis_issues")
    def test_single_file_workflow_with_issues(
        self, mock_get_issues: Mock, mock_analyze: Mock
    ) -> None:
        """Test complete workflow for single file with issues"""
        # Setup mocks
        mock_get_issues.return_value = [
            {
                "line": 1,
                "type": "code_smell",
                "severity": "MINOR",
                "message": "Test issue",
            }
        ]
        mock_analyze.return_value = "Analysis result"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('test')")
            temp_file = f.name

        try:
            # Create parser and parse args
            parser = _create_argument_parser()
            args = parser.parse_args([temp_file])

            # Process single file
            result = _process_single_file(args, temp_file)

            assert result == 0
            mock_get_issues.assert_called_once_with(temp_file)
            mock_analyze.assert_called_once()
        finally:
            os.unlink(temp_file)

    @patch("cli_file.analyze_file_with_ollama_sync")
    @patch("cli_file.get_static_analysis_issues")
    @pytest.mark.filterwarnings("ignore:coroutine.*was never awaited:RuntimeWarning")
    def test_single_file_workflow_no_issues(
        self, mock_get_issues: Mock, mock_analyze: Mock
    ) -> None:
        """Test complete workflow for single file without issues"""
        # Setup mocks
        mock_get_issues.return_value = []  # No issues

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# Clean code")
            temp_file = f.name

        try:
            # Create parser and parse args
            parser = _create_argument_parser()
            args = parser.parse_args([temp_file])

            # Process single file
            result = _process_single_file(args, temp_file)

            assert result == 0
            mock_get_issues.assert_called_once_with(temp_file)
            # Analyze should NOT be called when no issues
            mock_analyze.assert_not_called()
        finally:
            os.unlink(temp_file)

    @patch("cli_file.asyncio.run")
    @patch("cli_file.process_multiple_files_async")
    def test_multiple_files_workflow(
        self, mock_process_async: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test complete workflow for multiple files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = os.path.join(temp_dir, "file1.py")
            file2 = os.path.join(temp_dir, "file2.py")

            for f in [file1, file2]:
                with open(f, "w") as fd:
                    fd.write("# Test file")

            # Create parser and parse args
            parser = _create_argument_parser()
            args = parser.parse_args([file1, file2, "--concurrent", "2"])

            # Process multiple files
            result = _process_multiple_files(args, [file1, file2])

            assert result == 0
            mock_asyncio_run.assert_called_once()
            assert mock_process_async.called

    @pytest.mark.filterwarnings("ignore:coroutine.*was never awaited:RuntimeWarning")
    def test_output_to_markdown_workflow(self) -> None:
        """Test complete workflow with markdown output"""
        with (
            patch("cli_file.save_to_markdown") as mock_save,
            patch("cli_file.analyze_file_with_ollama_sync") as mock_analyze,
            patch("cli_file.get_static_analysis_issues") as mock_get_issues,
        ):

            # Setup mocks explicitly as regular Mock objects
            mock_get_issues.return_value = [
                {
                    "line": 1,
                    "type": "code_smell",
                    "severity": "MINOR",
                    "message": "Test issue",
                }
            ]
            mock_analyze.return_value = "# Analysis Report\n\nTest analysis"

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("print('test')")
                temp_file = f.name

            try:
                # Create parser with output flag
                parser = _create_argument_parser()
                args = parser.parse_args([temp_file, "--output"])

                # Process file
                result = _process_single_file(args, temp_file)

                assert result == 0
                mock_save.assert_called_once()
                # Verify save was called with correct arguments
                save_args = mock_save.call_args[0]
                assert save_args[1] == "# Analysis Report\n\nTest analysis"  # content
                assert save_args[2] == temp_file  # analyzed_file
            finally:
                os.unlink(temp_file)

    @patch("glob.glob")
    def test_glob_pattern_workflow(self, mock_glob: Mock) -> None:
        """Test complete workflow with glob patterns"""
        # Mock glob to return specific files
        mock_glob.return_value = ["src/file1.py", "src/file2.py"]

        # Test expansion
        expanded = _expand_file_patterns(["src/*.py"])

        assert len(expanded) == 2
        assert "src/file1.py" in expanded
        assert "src/file2.py" in expanded
        mock_glob.assert_called_once_with("src/*.py")

    def test_end_to_end_static_analysis(self) -> None:
        """Test end-to-end static analysis detection"""
        # Create a file with known issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """import unused_module
# TODO: Fix this later
print("Debug message")
password="hardcoded123"
try:
    risky_operation()
except:
    pass
"""
            )
            temp_file = f.name

        try:
            # Run static analysis
            issues = get_static_analysis_issues(temp_file)

            # Verify all issue types are detected
            issue_types = {issue["type"] for issue in issues}
            assert "code_smell" in issue_types  # TODO and print
            assert "vulnerability" in issue_types  # hardcoded password
            assert "bug" in issue_types  # empty except

            # Verify specific issues
            todo_issues = [i for i in issues if "TODO" in i["message"]]
            assert len(todo_issues) > 0

            print_issues = [i for i in issues if "logger" in i["message"]]
            assert len(print_issues) > 0

            password_issues = [i for i in issues if "credential" in i["message"]]
            assert len(password_issues) > 0
        finally:
            os.unlink(temp_file)


class TestAsyncProcessing:
    """Test async processing functions that weren't covered"""

    @pytest.mark.asyncio
    @patch("cli_file.analyze_file_with_ollama_async")
    @patch("cli_file.get_static_analysis_issues")
    @patch("cli_file.read_file_content")
    async def test_process_multiple_files_async_with_issues(
        self, mock_read: Mock, mock_get_issues: Mock, mock_analyze: Mock
    ) -> None:
        """Test process_multiple_files_async with files that have issues"""

        # Setup mocks
        mock_read.side_effect = ["print('file1')", "print('file2')"]
        mock_get_issues.side_effect = [
            [{"line": 1, "message": "issue1"}],  # file1 has issues
            [{"line": 1, "message": "issue2"}],  # file2 has issues
        ]
        mock_analyze.return_value = "Analysis result"

        # Test the function
        results = await process_multiple_files_async(
            host="http://localhost:11434",
            model="test-model",
            file_paths=["file1.py", "file2.py"],
            save_output=False,
            max_concurrent=2,
            stream_enabled=False,
        )

        # Verify results
        assert len(results) == 2
        assert all(r == "Analysis result" for r in results)
        assert mock_analyze.call_count == 2

    @pytest.mark.asyncio
    @patch("cli_file.get_static_analysis_issues")
    @patch("cli_file.read_file_content")
    async def test_process_multiple_files_async_no_issues(
        self, mock_read: Mock, mock_get_issues: Mock
    ) -> None:
        """Test process_multiple_files_async with files that have no issues"""
        # Setup mocks
        mock_read.side_effect = ["# clean file1", "# clean file2"]
        mock_get_issues.side_effect = [[], []]  # No issues

        # Test the function
        results = await process_multiple_files_async(
            host="http://localhost:11434",
            model="test-model",
            file_paths=["file1.py", "file2.py"],
            save_output=False,
            max_concurrent=2,
        )

        # Verify results - should be None for files with no issues
        assert len(results) == 2
        assert all(r is None for r in results)

    @pytest.mark.asyncio
    @patch("cli_file.read_file_content")
    async def test_process_multiple_files_async_read_error(
        self, mock_read: Mock
    ) -> None:
        """Test process_multiple_files_async with file read errors"""
        # Setup mock to return None (read error)
        mock_read.side_effect = [None, None]

        # Test the function
        results = await process_multiple_files_async(
            host="http://localhost:11434",
            model="test-model",
            file_paths=["bad1.py", "bad2.py"],
            save_output=False,
        )

        # Verify results - should be None for unreadable files
        assert len(results) == 2
        assert all(r is None for r in results)

    @pytest.mark.asyncio
    @patch("cli_file.save_to_markdown")
    @patch("cli_file.analyze_file_with_ollama_async")
    @patch("cli_file.get_static_analysis_issues")
    @patch("cli_file.read_file_content")
    @pytest.mark.filterwarnings("ignore:coroutine.*was never awaited:RuntimeWarning")
    async def test_process_multiple_files_async_with_save(
        self,
        mock_read: Mock,
        mock_get_issues: Mock,
        mock_analyze: Mock,
        mock_save: Mock,
    ) -> None:
        """Test process_multiple_files_async with save_output=True"""

        # Setup mocks
        mock_read.return_value = "print('test')"
        mock_get_issues.return_value = [{"line": 1, "message": "test issue"}]
        mock_analyze.return_value = "Analysis result"

        # Test with save_output=True
        results = await process_multiple_files_async(
            host="http://localhost:11434",
            model="test-model",
            file_paths=["test.py"],
            save_output=True,
            output_dir="/tmp/output",
        )

        # Verify save was called
        assert len(results) == 1
        assert results[0] == "Analysis result"
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    @patch("cli_file.analyze_file_with_ollama_async")
    @patch("cli_file.get_static_analysis_issues")
    @patch("cli_file.read_file_content")
    async def test_process_multiple_files_async_large_file(
        self, mock_read: Mock, mock_get_issues: Mock, mock_analyze: Mock
    ) -> None:
        """Test process_multiple_files_async with large file truncation"""

        # Setup large file content (> 100KB)
        large_content = "x" * 150000  # 150KB
        mock_read.return_value = large_content
        mock_get_issues.return_value = [{"line": 1, "message": "test issue"}]
        mock_analyze.return_value = "Analysis result"

        # Test the function
        results = await process_multiple_files_async(
            host="http://localhost:11434",
            model="test-model",
            file_paths=["large_file.py"],
            save_output=False,
        )

        # Verify file was processed and truncated content was passed to analyzer
        assert len(results) == 1
        assert results[0] == "Analysis result"

        # Check that analyze was called with truncated content
        # analyze_file_with_ollama_async(host, model, file_path, content,
        # is_streaming, sonar_issues, save_output)
        call_args = mock_analyze.call_args[0]  # Positional arguments
        truncated_content = call_args[3]  # 4th argument is content
        assert len(truncated_content) <= 100000 + 20  # 100KB + "... (truncated)"
        assert "... (truncated)" in truncated_content

    @pytest.mark.asyncio
    @patch("cli_file.analyze_file_with_ollama_async")
    @patch("cli_file.get_static_analysis_issues")
    @patch("cli_file.read_file_content")
    async def test_process_multiple_files_async_streaming(
        self, mock_read: Mock, mock_get_issues: Mock, mock_analyze: Mock
    ) -> None:
        """Test process_multiple_files_async with streaming enabled"""

        # Setup mocks
        mock_read.return_value = "print('test')"
        mock_get_issues.return_value = [{"line": 1, "message": "test issue"}]
        mock_analyze.return_value = "Analysis result"

        # Test with streaming enabled and no save_output
        await process_multiple_files_async(
            host="http://localhost:11434",
            model="test-model",
            file_paths=["test.py"],
            save_output=False,
            stream_enabled=True,
        )

        # Verify analyze was called with streaming=True
        # analyze_file_with_ollama_async(host, model, file_path, content,
        # is_streaming, sonar_issues, save_output)
        call_args = mock_analyze.call_args[0]  # Positional arguments
        assert call_args[4] is True  # 5th argument is is_streaming

        # Test with streaming enabled but save_output=True (should disable streaming)
        await process_multiple_files_async(
            host="http://localhost:11434",
            model="test-model",
            file_paths=["test.py"],
            save_output=True,
            stream_enabled=True,
        )

        # Verify analyze was called with streaming=False when saving output
        call_args = mock_analyze.call_args[0]  # Positional arguments
        assert call_args[4] is False  # 5th argument is is_streaming


class TestMainCliFile:
    """Test the main() function of cli_file.py"""

    @patch("cli_file._process_single_file")
    @patch("cli_file._validate_files")
    @patch("cli_file._expand_file_patterns")
    @patch("cli_file._configure_logging")
    @patch("cli_file._create_argument_parser")
    @patch("sys.argv", ["cli_file.py", "test.py"])
    def test_main_single_file_success(
        self,
        mock_parser: Mock,
        mock_logging: Mock,
        mock_expand: Mock,
        mock_validate: Mock,
        mock_process_single: Mock,
    ) -> None:
        """Test main() with single file processing"""
        from cli_file import main

        # Setup mocks
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.file = ["test.py"]

        mock_parser.return_value.parse_args.return_value = mock_args
        mock_expand.return_value = ["test.py"]
        mock_validate.return_value = ["test.py"]  # Single valid file
        mock_process_single.return_value = 0

        # Test main function
        result = main()

        # Verify workflow
        assert result == 0
        mock_parser.assert_called_once()
        mock_logging.assert_called_once_with(False)
        mock_expand.assert_called_once_with(["test.py"])
        mock_validate.assert_called_once_with(["test.py"])
        mock_process_single.assert_called_once_with(mock_args, "test.py")

    @patch("cli_file._process_multiple_files")
    @patch("cli_file._validate_files")
    @patch("cli_file._expand_file_patterns")
    @patch("cli_file._configure_logging")
    @patch("cli_file._create_argument_parser")
    @patch("sys.argv", ["cli_file.py", "file1.py", "file2.py"])
    def test_main_multiple_files_success(
        self,
        mock_parser: Mock,
        mock_logging: Mock,
        mock_expand: Mock,
        mock_validate: Mock,
        mock_process_multiple: Mock,
    ) -> None:
        """Test main() with multiple files processing"""
        from cli_file import main

        # Setup mocks
        mock_args = Mock()
        mock_args.verbose = True
        mock_args.file = ["file1.py", "file2.py"]

        mock_parser.return_value.parse_args.return_value = mock_args
        mock_expand.return_value = ["file1.py", "file2.py"]
        mock_validate.return_value = ["file1.py", "file2.py"]  # Multiple valid files
        mock_process_multiple.return_value = 0

        # Test main function
        result = main()

        # Verify workflow
        assert result == 0
        mock_parser.assert_called_once()
        mock_logging.assert_called_once_with(True)  # Verbose mode
        mock_expand.assert_called_once_with(["file1.py", "file2.py"])
        mock_validate.assert_called_once_with(["file1.py", "file2.py"])
        mock_process_multiple.assert_called_once_with(
            mock_args, ["file1.py", "file2.py"]
        )

    @patch("cli_file._validate_files")
    @patch("cli_file._expand_file_patterns")
    @patch("cli_file._configure_logging")
    @patch("cli_file._create_argument_parser")
    @patch("sys.argv", ["cli_file.py", "nonexistent.py"])
    def test_main_no_valid_files(
        self,
        mock_parser: Mock,
        mock_logging: Mock,
        mock_expand: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test main() when no valid files are found"""
        from cli_file import main

        # Setup mocks
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.file = ["nonexistent.py"]

        mock_parser.return_value.parse_args.return_value = mock_args
        mock_expand.return_value = ["nonexistent.py"]
        mock_validate.return_value = None  # No valid files

        # Test main function
        result = main()

        # Verify error handling
        assert result == 1
        mock_parser.assert_called_once()
        mock_logging.assert_called_once_with(False)
        mock_expand.assert_called_once_with(["nonexistent.py"])
        mock_validate.assert_called_once_with(["nonexistent.py"])

    @patch("cli_file._process_single_file")
    @patch("cli_file._validate_files")
    @patch("cli_file._expand_file_patterns")
    @patch("cli_file._configure_logging")
    @patch("cli_file._create_argument_parser")
    @patch("sys.argv", ["cli_file.py", "*.py", "--verbose"])
    def test_main_with_glob_patterns(
        self,
        mock_parser: Mock,
        mock_logging: Mock,
        mock_expand: Mock,
        mock_validate: Mock,
        mock_process_single: Mock,
    ) -> None:
        """Test main() with glob patterns"""
        from cli_file import main

        # Setup mocks
        mock_args = Mock()
        mock_args.verbose = True
        mock_args.file = ["*.py"]

        mock_parser.return_value.parse_args.return_value = mock_args
        mock_expand.return_value = ["file1.py", "file2.py", "file3.py"]  # Glob expanded
        mock_validate.return_value = ["file1.py"]  # Only one valid after validation
        mock_process_single.return_value = 0

        # Test main function
        result = main()

        # Verify glob handling and fallback to single file processing
        assert result == 0
        mock_expand.assert_called_once_with(["*.py"])
        mock_validate.assert_called_once_with(["file1.py", "file2.py", "file3.py"])
        mock_process_single.assert_called_once_with(mock_args, "file1.py")

    @patch("cli_file._process_multiple_files")
    @patch("cli_file._validate_files")
    @patch("cli_file._expand_file_patterns")
    @patch("cli_file._configure_logging")
    @patch("cli_file._create_argument_parser")
    @patch("sys.argv", ["cli_file.py", "src/*.py", "--concurrent", "8"])
    def test_main_integration_workflow(
        self,
        mock_parser: Mock,
        mock_logging: Mock,
        mock_expand: Mock,
        mock_validate: Mock,
        mock_process_multiple: Mock,
    ) -> None:
        """Test main() complete integration workflow"""
        from cli_file import main

        # Setup realistic mocks
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.file = ["src/*.py"]
        mock_args.concurrent = 8

        mock_parser.return_value.parse_args.return_value = mock_args
        mock_expand.return_value = ["src/module1.py", "src/module2.py", "src/utils.py"]
        mock_validate.return_value = [
            "src/module1.py",
            "src/module2.py",
        ]  # 2 valid files
        mock_process_multiple.return_value = 0

        # Test main function
        result = main()

        # Verify complete workflow
        assert result == 0

        # Verify each step was called correctly
        mock_parser.assert_called_once()
        mock_parser.return_value.parse_args.assert_called_once()
        mock_logging.assert_called_once_with(False)
        mock_expand.assert_called_once_with(["src/*.py"])
        mock_validate.assert_called_once_with(
            ["src/module1.py", "src/module2.py", "src/utils.py"]
        )
        mock_process_multiple.assert_called_once_with(
            mock_args, ["src/module1.py", "src/module2.py"]
        )
