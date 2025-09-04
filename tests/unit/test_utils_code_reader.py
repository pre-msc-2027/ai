"""
Unit tests for the code reader utilities module
"""

import os
from pathlib import Path
import tempfile
from unittest.mock import mock_open, patch

import pytest

from src.utils.code_reader import extract_code_snippet


class TestExtractCodeSnippet:
    """Test code snippet extraction functionality"""

    def test_extract_code_snippet_normal_case(self):
        """Test extracting code snippet with normal context"""
        file_content = "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 4, context=2)
            assert result == "line 2\nline 3\nline 4\nline 5\nline 6"

    def test_extract_code_snippet_beginning_of_file(self):
        """Test extracting code at the beginning of file"""
        file_content = "line 1\nline 2\nline 3\nline 4\nline 5"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 2, context=3)
            assert result == "line 1\nline 2\nline 3\nline 4\nline 5"

    def test_extract_code_snippet_end_of_file(self):
        """Test extracting code at the end of file"""
        file_content = "line 1\nline 2\nline 3\nline 4\nline 5"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 4, context=3)
            assert result == "line 1\nline 2\nline 3\nline 4\nline 5"

    def test_extract_code_snippet_single_line_file(self):
        """Test extracting from a single line file"""
        file_content = "single line content"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 1, context=5)
            assert result == "single line content"

    def test_extract_code_snippet_exact_line(self):
        """Test extracting with zero context"""
        file_content = "line 1\nline 2\nline 3\nline 4\nline 5"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 3, context=0)
            assert result == "line 3"

    def test_extract_code_snippet_large_context(self):
        """Test extracting with context larger than file"""
        file_content = "line 1\nline 2\nline 3"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 2, context=100)
            assert result == "line 1\nline 2\nline 3"

    def test_extract_code_snippet_empty_file(self):
        """Test extracting from an empty file"""
        file_content = ""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("empty.py", 1, context=2)
            assert result == ""

    def test_extract_code_snippet_file_not_found(self):
        """Test handling of non-existent file"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = extract_code_snippet("nonexistent.py", 1)
            assert "Fichier non trouvé" in result

    def test_extract_code_snippet_unicode_error(self):
        """Test handling of unicode decode errors"""
        with patch(
            "builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "")
        ):
            result = extract_code_snippet("binary.bin", 1)
            assert "Code non disponible (erreur de lecture)" in result

    def test_extract_code_snippet_permission_error(self):
        """Test handling of permission errors"""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = extract_code_snippet("protected.py", 1)
            assert "Code non disponible (erreur de lecture)" in result

    def test_extract_code_snippet_generic_error(self):
        """Test handling of generic exceptions"""
        with patch("builtins.open", side_effect=Exception("Unknown error")):
            result = extract_code_snippet("error.py", 1)
            assert "Code non disponible (erreur de lecture)" in result

    def test_extract_code_snippet_with_workspace_absolute_path(self):
        """Test extraction with workspace when file path is absolute"""
        file_content = "workspace file content"
        test_file = "/absolute/path/to/file.py"

        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet(test_file, 1, workspace="/workspace")
            assert result == "workspace file content"

    def test_extract_code_snippet_with_workspace_relative_path(self):
        """Test extraction with workspace when file path is relative"""
        file_content = "relative file content"

        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            result = extract_code_snippet("src/module.py", 1, workspace="/workspace")
            assert result == "relative file content"
            # Check that workspace was prepended to relative path
            mock_file.assert_called_with(
                "/workspace/src/module.py", "r", encoding="utf-8"
            )

    def test_extract_code_snippet_no_workspace(self):
        """Test extraction without workspace parameter"""
        file_content = "no workspace content"

        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            result = extract_code_snippet("local_file.py", 1)
            assert result == "no workspace content"
            # Check that file was opened with original path
            mock_file.assert_called_with("local_file.py", "r", encoding="utf-8")

    def test_extract_code_snippet_line_out_of_range(self):
        """Test extracting with line number beyond file length"""
        file_content = "line 1\nline 2\nline 3"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 10, context=2)
            # Should handle gracefully and return available lines
            assert result in ["line 1\nline 2\nline 3", ""]

    def test_extract_code_snippet_negative_line_number(self):
        """Test extracting with negative line number"""
        file_content = "line 1\nline 2\nline 3"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", -1, context=1)
            # Should handle gracefully
            assert result == "line 1\nline 2\nline 3"

    def test_extract_code_snippet_with_tabs(self):
        """Test extracting code with tab characters"""
        file_content = "def func():\n\tx = 10\n\treturn x"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 2, context=1)
            assert "\tx = 10" in result

    def test_extract_code_snippet_with_windows_line_endings(self):
        """Test extracting code with Windows line endings"""
        file_content = "line 1\r\nline 2\r\nline 3\r\nline 4"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 2, context=1)
            # Should handle different line endings
            assert "line 2" in result

    def test_extract_code_snippet_with_mixed_line_endings(self):
        """Test extracting code with mixed line endings"""
        file_content = "line 1\nline 2\r\nline 3\rline 4"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 2, context=1)
            assert "line 2" in result

    def test_extract_code_snippet_with_no_newline_at_eof(self):
        """Test extracting from file without newline at end"""
        file_content = "line 1\nline 2\nno newline at end"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 3, context=1)
            assert "no newline at end" in result

    def test_extract_code_snippet_real_file(self, tmp_path):
        """Test with actual file on filesystem"""
        # Create a real temporary file
        test_file = tmp_path / "real_test.py"
        test_content = """def test_function():
    # This is line 2
    x = 10  # Target line 3
    y = 20
    return x + y"""
        test_file.write_text(test_content)

        result = extract_code_snippet(str(test_file), 3, context=1)

        assert "# This is line 2" in result
        assert "x = 10" in result
        assert "y = 20" in result

    def test_extract_code_snippet_workspace_with_real_files(self, tmp_path):
        """Test workspace functionality with real files"""
        # Create workspace structure
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        src_dir = workspace / "src"
        src_dir.mkdir()

        module_file = src_dir / "module.py"
        module_content = """import os

def process_data():
    data = [1, 2, 3]
    return sum(data)"""
        module_file.write_text(module_content)

        # Test with workspace parameter
        result = extract_code_snippet(
            "src/module.py", 4, context=2, workspace=str(workspace)
        )

        assert "def process_data():" in result
        assert "data = [1, 2, 3]" in result
        assert "return sum(data)" in result

    @patch("logging.warning")
    def test_extract_code_snippet_logs_file_not_found(self, mock_log):
        """Test that file not found is logged"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            extract_code_snippet("missing.py", 1)
            mock_log.assert_called_once()
            assert "Fichier non trouvé" in str(mock_log.call_args)

    @patch("logging.warning")
    def test_extract_code_snippet_logs_other_errors(self, mock_log):
        """Test that other errors are logged"""
        with patch("builtins.open", side_effect=Exception("Test error")):
            extract_code_snippet("error.py", 1)
            mock_log.assert_called_once()
            assert "Test error" in str(mock_log.call_args)

    def test_extract_code_snippet_special_characters(self):
        """Test extracting code with special characters"""
        file_content = (
            "# -*- coding: utf-8 -*-\n# Spéçiäl chàracters: 🐍 émoji\nprint('Hello, 世界')"
        )
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("special.py", 2, context=1)
            assert "Spéçiäl" in result
            assert "🐍" in result
            assert "世界" in result
