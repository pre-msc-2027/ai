"""
Unit tests for the prompt builder module
"""

import pytest

from src.prompt_builder import build_prompt


class TestBuildPrompt:
    """Test prompt building functionality"""

    def test_build_prompt_basic(self):
        """Test basic prompt building"""
        code_snippet = "import unused_module"
        rule = {
            "name": "Unused Import",
            "Description": "Remove unused imports",
            "language": "python",
            "parameters": {},
        }
        file_path = "test.py"
        line_number = 10

        result = build_prompt(code_snippet, rule, file_path, line_number)

        # Check key components are in the prompt
        assert "python" in result
        assert "test.py" in result
        assert "10" in str(result)
        assert "Unused Import" in result
        assert "Remove unused imports" in result
        assert code_snippet in result
        assert '{"original":' in result
        assert '"fixed":' in result

    def test_build_prompt_with_parameters(self):
        """Test prompt building with rule parameters"""
        code_snippet = "console.log('test')"
        rule = {
            "name": "Console Usage",
            "description": "Replace console with logger",
            "language": "javascript",
            "parameters": {"level": "warning", "format": "json"},
        }
        file_path = "app.js"
        line_number = 25

        result = build_prompt(code_snippet, rule, file_path, line_number)

        assert "javascript" in result
        assert "app.js" in result
        assert "25" in str(result)
        assert "Console Usage" in result
        assert "Rule parameters" in result
        assert "level" in result
        assert "warning" in result

    def test_build_prompt_missing_description(self):
        """Test prompt building with missing description"""
        code_snippet = "test code"
        rule = {
            "name": "Test Rule",
            # No Description or description field
            "language": "python",
            "parameters": {},
        }
        file_path = "test.py"
        line_number = 1

        result = build_prompt(code_snippet, rule, file_path, line_number)

        assert "No description available" in result

    def test_build_prompt_description_lowercase(self):
        """Test prompt building with lowercase description key"""
        code_snippet = "test code"
        rule = {
            "name": "Test Rule",
            "description": "This is lowercase description",
            "language": "python",
            "parameters": {},
        }
        file_path = "test.py"
        line_number = 1

        result = build_prompt(code_snippet, rule, file_path, line_number)

        assert "This is lowercase description" in result

    def test_build_prompt_description_uppercase(self):
        """Test prompt building with uppercase Description key"""
        code_snippet = "test code"
        rule = {
            "name": "Test Rule",
            "Description": "This is uppercase Description",
            "language": "python",
            "parameters": {},
        }
        file_path = "test.py"
        line_number = 1

        result = build_prompt(code_snippet, rule, file_path, line_number)

        assert "This is uppercase Description" in result

    def test_build_prompt_missing_name(self):
        """Test prompt building with missing rule name"""
        code_snippet = "test code"
        rule = {
            # No name field
            "description": "Test description",
            "language": "python",
            "parameters": {},
        }
        file_path = "test.py"
        line_number = 1

        result = build_prompt(code_snippet, rule, file_path, line_number)

        assert "Unknown rule" in result

    def test_build_prompt_missing_language(self):
        """Test prompt building with missing language"""
        code_snippet = "test code"
        rule = {
            "name": "Test Rule",
            "description": "Test description",
            # No language field
            "parameters": {},
        }
        file_path = "test.py"
        line_number = 1

        result = build_prompt(code_snippet, rule, file_path, line_number)

        assert "unknown" in result.lower()

    def test_build_prompt_empty_parameters(self):
        """Test prompt building with empty parameters"""
        code_snippet = "test code"
        rule = {
            "name": "Test Rule",
            "description": "Test description",
            "language": "python",
            "parameters": {},
        }
        file_path = "test.py"
        line_number = 1

        result = build_prompt(code_snippet, rule, file_path, line_number)

        # Should not include parameters section
        assert "Rule parameters" not in result

    def test_build_prompt_none_parameters(self):
        """Test prompt building with None parameters"""
        code_snippet = "test code"
        rule = {
            "name": "Test Rule",
            "description": "Test description",
            "language": "python",
            "parameters": None,
        }
        file_path = "test.py"
        line_number = 1

        result = build_prompt(code_snippet, rule, file_path, line_number)

        # Should not include parameters section
        assert "Rule parameters" not in result

    def test_build_prompt_multiline_code(self):
        """Test prompt building with multiline code snippet"""
        code_snippet = """def function():
    x = 10
    print(x)  # Problem here
    return x"""

        rule = {
            "name": "Print Statement",
            "description": "Replace print with logger",
            "language": "python",
            "parameters": {},
        }
        file_path = "module.py"
        line_number = 3

        result = build_prompt(code_snippet, rule, file_path, line_number)

        assert code_snippet in result
        assert "```python" in result

    def test_build_prompt_special_characters(self):
        """Test prompt building with special characters"""
        code_snippet = "const émoji = '🐍'; // spéçiäl"
        rule = {
            "name": "Règle spéciale",
            "description": "Description avec caractères spéciaux: é, à, ç",
            "language": "javascript",
            "parameters": {"key": "valeur spéciale"},
        }
        file_path = "spécial.js"
        line_number = 42

        result = build_prompt(code_snippet, rule, file_path, line_number)

        assert "émoji" in result
        assert "spéçiäl" in result
        assert "Règle spéciale" in result
        assert "caractères spéciaux" in result

    def test_build_prompt_structure(self):
        """Test the structure of the generated prompt"""
        code_snippet = "test"
        rule = {
            "name": "Rule",
            "description": "Desc",
            "language": "python",
            "parameters": {},
        }

        result = build_prompt(code_snippet, rule, "file.py", 1)

        # Check structure elements
        assert "You are a" in result
        assert "**Identified Problem:**" in result
        assert "**Code in question:**" in result
        assert "**Instructions:**" in result
        assert "1. Identify the exact line" in result
        assert "2. Provide a correction" in result
        assert "3. Return ONLY valid JSON" in result

    def test_build_prompt_json_format_instruction(self):
        """Test that JSON format instruction is included"""
        code_snippet = "test"
        rule = {
            "name": "Rule",
            "description": "Desc",
            "language": "python",
            "parameters": {},
        }

        result = build_prompt(code_snippet, rule, "file.py", 1)

        # Check JSON format example is included
        assert '{"original":' in result
        assert '"fixed":' in result
        assert "valid JSON" in result

    def test_build_prompt_complex_parameters(self):
        """Test prompt building with complex nested parameters"""
        code_snippet = "code"
        rule = {
            "name": "Complex Rule",
            "description": "Complex description",
            "language": "python",
            "parameters": {
                "level": "error",
                "options": {"strict": True, "mode": "advanced"},
                "thresholds": [10, 20, 30],
            },
        }
        file_path = "complex.py"
        line_number = 100

        result = build_prompt(code_snippet, rule, file_path, line_number)

        assert "Rule parameters" in result
        # Parameters should be converted to string representation
        assert "level" in result
        assert "options" in result
        assert "thresholds" in result
