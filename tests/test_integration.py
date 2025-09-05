"""
Integration tests for SecuScan AI - testing complete workflows
"""

from io import StringIO
import json
import sys
from unittest.mock import Mock, call, patch

import pytest

from src.api.issues import get_analysis_data
from src.main import main
from src.ollama.client import send_prompt_to_ollama
from src.prompt_builder import build_prompt
from src.utils.code_reader import extract_code_snippet


class TestCompleteWorkflow:
    """Test complete application workflows end-to-end"""

    @patch("src.main.post_ai_comment")
    @patch("src.main.get_analysis_data")
    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.extract_code_snippet")
    @patch("sys.argv", ["main.py", "--scan-id", "integration-test"])
    def test_single_warning_successful_fix(
        self, mock_extract, mock_ollama, mock_get_data, mock_post_api, capsys
    ):
        """Test complete flow with a single warning that gets fixed"""
        # Setup mock data
        mock_get_data.return_value = (
            [{"id": 1, "rule_id": 1, "file": "test.py", "line": 10}],
            [
                {
                    "rule_id": 1,
                    "name": "Import Rule",
                    "description": "Fix imports",
                    "language": "python",
                    "parameters": {},
                }
            ],
            "/workspace",
        )
        mock_extract.return_value = "import unused"
        mock_ollama.return_value = '{"original": "import unused", "fixed": ""}'
        mock_post_api.return_value = True  # API call succeeds

        # Run main
        main()

        # Verify API was called with correct data
        mock_post_api.assert_called_once()
        call_args = mock_post_api.call_args
        assert call_args[0][0] == "integration-test"  # scan_id

        result = call_args[0][1]  # AI results
        assert len(result) == 1
        assert result[0]["warning_id"] == 1
        assert result[0]["original"] == "import unused"
        assert result[0]["fixed"] == ""

    @patch("src.main.post_ai_comment")
    @patch("src.main.get_analysis_data")
    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.extract_code_snippet")
    @patch("sys.argv", ["main.py", "--scan-id", "multi-test", "--verbose"])
    def test_multiple_warnings_mixed_results(
        self, mock_extract, mock_ollama, mock_get_data, mock_post_api, capsys
    ):
        """Test workflow with multiple warnings, some succeed, some fail"""
        # Setup mock data
        warnings = [
            {"id": 1, "rule_id": 1, "file": "file1.py", "line": 10},
            {"id": 2, "rule_id": 2, "file": "file2.py", "line": 20},
            {"id": 3, "rule_id": 1, "file": "file3.py", "line": 30},
        ]
        rules = [
            {
                "rule_id": 1,
                "name": "Rule1",
                "description": "Desc1",
                "language": "python",
                "parameters": {},
            },
            {
                "rule_id": 2,
                "name": "Rule2",
                "description": "Desc2",
                "language": "python",
                "parameters": {"strict": True},
            },
        ]

        mock_get_data.return_value = (warnings, rules, "/workspace")
        mock_extract.return_value = "code snippet"
        mock_post_api.return_value = True

        # First and third succeed, second fails
        mock_ollama.side_effect = [
            '{"original": "bad1", "fixed": "good1"}',
            "Invalid JSON response",
            '{"original": "bad3", "fixed": "good3"}',
        ]

        # Run main
        main()

        # Verify API was called with correct data
        mock_post_api.assert_called_once()
        call_args = mock_post_api.call_args
        assert call_args[0][0] == "multi-test"  # scan_id

        result = call_args[0][1]  # AI results
        assert len(result) == 2
        assert result[0]["warning_id"] == 1
        assert result[0]["fixed"] == "good1"
        assert result[1]["warning_id"] == 3
        assert result[1]["fixed"] == "good3"

    @patch("src.main.post_ai_comment")
    @patch("src.main.get_analysis_data")
    @patch("sys.argv", ["main.py", "--scan-id", "no-warnings-test"])
    def test_no_warnings_empty_output(self, mock_get_data, mock_post_api, capsys):
        """Test workflow when no warnings are found"""
        mock_get_data.return_value = ([], [], "/workspace")
        mock_post_api.return_value = True

        main()

        # Verify API was called with empty results
        mock_post_api.assert_called_once_with("no-warnings-test", [])

    @patch("src.main.post_ai_comment")
    @patch("src.main.get_analysis_data")
    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.extract_code_snippet")
    @patch("sys.argv", ["main.py", "--scan-id", "error-recovery-test"])
    def test_error_recovery_workflow(
        self, mock_extract, mock_ollama, mock_get_data, mock_post_api, capsys
    ):
        """Test that workflow continues despite individual errors"""
        warnings = [
            {"id": 1, "rule_id": 1, "file": "file1.py", "line": 10},
            {"id": 2, "rule_id": 999, "file": "file2.py", "line": 20},  # Missing rule
            {"id": 3, "rule_id": 1, "file": "file3.py", "line": 30},
        ]
        rules = [
            {
                "rule_id": 1,
                "name": "Rule1",
                "description": "Desc1",
                "language": "python",
                "parameters": {},
            }
        ]

        mock_get_data.return_value = (warnings, rules, "/workspace")
        mock_extract.return_value = "code"
        mock_ollama.return_value = '{"original": "code", "fixed": "fixed"}'
        mock_post_api.return_value = True

        main()

        # Verify API was called with correct data
        mock_post_api.assert_called_once()
        call_args = mock_post_api.call_args
        assert call_args[0][0] == "error-recovery-test"  # scan_id

        result = call_args[0][1]  # AI results
        # Should process warnings 1 and 3, skip 2 (missing rule)
        assert len(result) == 2
        assert result[0]["warning_id"] == 1
        assert result[1]["warning_id"] == 3


class TestAPIToOllamaIntegration:
    """Test integration between API and Ollama components"""

    @patch("requests.get")
    @patch("ollama.Client")
    def test_api_data_flows_to_ollama(self, mock_ollama_client, mock_requests):
        """Test that API data correctly flows through to Ollama"""
        # Setup API response
        api_response = {
            "analysis": {
                "warnings": [{"id": 1, "rule_id": 1, "file": "test.py", "line": 5}],
                "repo_url": "https://github.com/test/repo",
            },
            "rules": [
                {
                    "rule_id": 1,
                    "name": "TestRule",
                    "description": "Test",
                    "language": "python",
                    "parameters": {},
                }
            ],
        }

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.json.return_value = api_response
        mock_requests.return_value = mock_resp

        # Get data from API
        warnings, rules, workspace = get_analysis_data("test-scan")

        assert len(warnings) == 1
        assert len(rules) == 1
        assert workspace == "folder/repo"

        # Build prompt with API data
        prompt = build_prompt(
            "test code", rules[0], warnings[0]["file"], warnings[0]["line"]
        )

        assert "TestRule" in prompt
        assert "test.py" in prompt
        assert "5" in str(prompt)

        # Send to Ollama
        mock_client = Mock()
        mock_ollama_client.return_value = mock_client
        mock_client.chat.return_value = {"message": {"content": "response"}}

        result = send_prompt_to_ollama(prompt, "model", "host")

        assert result == "response"


class TestPerformanceWithManyWarnings:
    """Test system performance with large numbers of warnings"""

    @patch("src.main.post_ai_comment")
    @patch("src.main.get_analysis_data")
    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.extract_code_snippet")
    @patch("sys.argv", ["main.py", "--scan-id", "performance-test"])
    def test_hundred_warnings(
        self, mock_extract, mock_ollama, mock_get_data, mock_post_api, capsys
    ):
        """Test processing 100 warnings"""
        # Generate 100 warnings
        warnings = [
            {"id": i, "rule_id": i % 5, "file": f"file{i}.py", "line": i * 10}
            for i in range(100)
        ]

        # Generate 5 different rules
        rules = [
            {
                "rule_id": i,
                "name": f"Rule{i}",
                "description": f"Description {i}",
                "language": "python",
                "parameters": {},
            }
            for i in range(5)
        ]

        mock_get_data.return_value = (warnings, rules, "/workspace")
        mock_extract.return_value = "code"
        mock_post_api.return_value = True

        # 80% success rate
        responses = []
        for i in range(100):
            if i % 5 == 0:
                responses.append("Invalid JSON")
            else:
                responses.append(f'{{"original": "bad{i}", "fixed": "good{i}"}}')
        mock_ollama.side_effect = responses

        main()

        # Verify API was called with correct data
        mock_post_api.assert_called_once()
        call_args = mock_post_api.call_args
        assert call_args[0][0] == "performance-test"  # scan_id

        result = call_args[0][1]  # AI results
        # Should have 80 successful fixes
        assert len(result) == 80

        # Verify all successful ones have correct structure
        for fix in result:
            assert "warning_id" in fix
            assert "original" in fix
            assert "fixed" in fix


class TestDifferentLanguages:
    """Test handling of different programming languages"""

    @patch("src.main.post_ai_comment")
    @patch("src.main.get_analysis_data")
    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.extract_code_snippet")
    @patch("sys.argv", ["main.py", "--scan-id", "multilang-test"])
    def test_multiple_languages(
        self, mock_extract, mock_ollama, mock_get_data, mock_post_api, capsys
    ):
        """Test processing warnings for different languages"""
        warnings = [
            {"id": 1, "rule_id": 1, "file": "test.py", "line": 10},
            {"id": 2, "rule_id": 2, "file": "test.js", "line": 20},
            {"id": 3, "rule_id": 3, "file": "test.java", "line": 30},
        ]

        rules = [
            {
                "rule_id": 1,
                "name": "Python Rule",
                "description": "Python specific",
                "language": "python",
                "parameters": {},
            },
            {
                "rule_id": 2,
                "name": "JS Rule",
                "description": "JavaScript specific",
                "language": "javascript",
                "parameters": {},
            },
            {
                "rule_id": 3,
                "name": "Java Rule",
                "description": "Java specific",
                "language": "java",
                "parameters": {},
            },
        ]

        mock_get_data.return_value = (warnings, rules, "/workspace")
        mock_post_api.return_value = True

        # Different code for each language
        mock_extract.side_effect = [
            "import unused_module",
            "console.log('debug');",
            'System.out.println("debug");',
        ]

        mock_ollama.side_effect = [
            '{"original": "import unused_module", "fixed": ""}',
            (
                '{"original": "console.log(\'debug\');", '
                '"fixed": "logger.debug(\'debug\');"}'
            ),
            (
                '{"original": "System.out.println(\\"debug\\");", '
                '"fixed": "logger.debug(\\"debug\\");"}'
            ),
        ]

        main()

        # Verify API was called with correct data
        mock_post_api.assert_called_once()
        call_args = mock_post_api.call_args
        assert call_args[0][0] == "multilang-test"  # scan_id

        result = call_args[0][1]  # AI results
        assert len(result) == 3
        assert result[0]["fixed"] == ""
        assert "logger.debug" in result[1]["fixed"]
        assert "logger.debug" in result[2]["fixed"]


class TestEnvironmentConfiguration:
    """Test environment-based configuration"""

    @patch("src.main.post_ai_comment")
    @patch("src.main.get_analysis_data")
    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.extract_code_snippet")
    @patch.dict(
        "os.environ",
        {
            "OLLAMA_HOST": "http://env-host:11434",
            "OLLAMA_MODEL": "env-model:latest",
            "API_BASE_URL": "http://env-api:8000",
        },
    )
    @patch("sys.argv", ["main.py", "--scan-id", "env-test"])
    def test_env_variables_used(
        self, mock_extract, mock_ollama, mock_get_data, mock_post_api
    ):
        """Test that environment variables are properly used"""
        mock_get_data.return_value = (
            [{"id": 1, "rule_id": 1, "file": "test.py", "line": 10}],
            [
                {
                    "rule_id": 1,
                    "name": "Rule",
                    "description": "Desc",
                    "language": "python",
                    "parameters": {},
                }
            ],
            "/workspace",
        )
        mock_extract.return_value = "code"
        mock_ollama.return_value = '{"original": "code", "fixed": "fixed"}'
        mock_post_api.return_value = True

        main()

        # Check that env variables were used
        mock_ollama.assert_called_with(
            prompt=mock_ollama.call_args[1]["prompt"],
            model="env-model:latest",
            host="http://env-host:11434",
        )


class TestVerboseMode:
    """Test verbose mode logging and output"""

    @patch("src.main.post_ai_comment")
    @patch("src.main.get_analysis_data")
    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.extract_code_snippet")
    @patch("logging.info")
    @patch("sys.argv", ["main.py", "--scan-id", "verbose-test", "--verbose"])
    def test_verbose_logging(
        self, mock_log_info, mock_extract, mock_ollama, mock_get_data, mock_post_api
    ):
        """Test that verbose mode produces detailed logging"""
        mock_get_data.return_value = (
            [{"id": 1, "rule_id": 1, "file": "test.py", "line": 10}],
            [
                {
                    "rule_id": 1,
                    "name": "Rule",
                    "description": "Desc",
                    "language": "python",
                    "parameters": {},
                }
            ],
            "/workspace",
        )
        mock_extract.return_value = "code"
        mock_ollama.return_value = '{"original": "code", "fixed": "fixed"}'
        mock_post_api.return_value = True

        main()

        # Check verbose logging occurred
        log_messages = [str(call) for call in mock_log_info.call_args_list]
        assert any("verbose-test" in msg for msg in log_messages)
        assert any("1 warnings" in msg for msg in log_messages)
