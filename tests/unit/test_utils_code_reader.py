from unittest.mock import mock_open, patch

import pytest

from src.utils.code_reader import extract_code_snippet


class TestExtractCodeSnippet:
    def test_extract_code_snippet_normal_case(self):
        file_content = "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 4, context=2)
            assert result == "line 2\nline 3\nline 4\nline 5\nline 6"

    def test_extract_code_snippet_beginning_of_file(self):
        file_content = "line 1\nline 2\nline 3\nline 4\nline 5"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 2, context=3)
            assert result == "line 1\nline 2\nline 3\nline 4\nline 5"

    def test_extract_code_snippet_end_of_file(self):
        file_content = "line 1\nline 2\nline 3\nline 4\nline 5"
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = extract_code_snippet("test.py", 4, context=3)
            assert result == "line 1\nline 2\nline 3\nline 4\nline 5"

    def test_extract_code_snippet_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = extract_code_snippet("nonexistent.py", 1)
            assert result == "# Code non disponible (erreur de lecture)"

    def test_extract_code_snippet_unicode_error(self):
        with patch(
            "builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "")
        ):
            result = extract_code_snippet("binary.bin", 1)
            assert result == "# Code non disponible (erreur de lecture)"
