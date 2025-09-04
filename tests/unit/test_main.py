"""
Unit tests for the main module
"""

from io import StringIO
import json
import sys
from unittest.mock import Mock, call, patch

import pytest

from src.main import (
    log_startup_info,
    main,
    parse_arguments,
    parse_json_response,
    process_warning,
    setup_logging,
)


class TestParseJsonResponse:
    """Test JSON response parsing functionality"""

    def test_parse_valid_json_direct(self):
        """Test parsing clean JSON response"""
        response = '{"original": "import unused", "fixed": ""}'
        result = parse_json_response(response)
        assert result == {"original": "import unused", "fixed": ""}

    def test_parse_json_with_whitespace(self):
        """Test parsing JSON with extra whitespace"""
        response = '  \n{"original": "print(x)", "fixed": "logger.info(x)"}\n  '
        result = parse_json_response(response)
        assert result == {"original": "print(x)", "fixed": "logger.info(x)"}

    def test_parse_json_embedded_in_text(self):
        """Test extracting JSON from text"""
        response = (
            'Here is the fix:\n{"original": "console.log()", '
            '"fixed": "logger.debug()"}\nDone!'
        )
        result = parse_json_response(response)
        assert result == {"original": "console.log()", "fixed": "logger.debug()"}

    def test_parse_invalid_json(self):
        """Test handling of invalid JSON"""
        response = "This is not JSON at all"
        result = parse_json_response(response)
        assert result is None

    def test_parse_malformed_json(self):
        """Test handling of malformed JSON"""
        response = '{"original": "test", "fixed": '  # Missing closing
        result = parse_json_response(response)
        assert result is None


class TestProcessWarning:
    """Test warning processing functionality"""

    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.build_prompt")
    @patch("src.main.extract_code_snippet")
    def test_process_warning_success(
        self, mock_extract, mock_build, mock_ollama, test_args, mock_rules
    ):
        """Test successful warning processing"""
        # Setup mocks
        mock_extract.return_value = "import unused"
        mock_build.return_value = "test prompt"
        mock_ollama.return_value = '{"original": "import unused", "fixed": ""}'

        warning = {"id": 0, "rule_id": 0, "file": "test.py", "line": 10}
        rules_dict = {rule["rule_id"]: rule for rule in mock_rules}

        # Process warning
        result = process_warning(warning, rules_dict, "/workspace", test_args)

        # Assertions
        assert result is not None
        assert result["warning_id"] == 0
        assert result["original"] == "import unused"
        assert result["fixed"] == ""
        mock_extract.assert_called_once_with("test.py", 10, workspace="/workspace")
        mock_build.assert_called_once()
        mock_ollama.assert_called_once()

    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.extract_code_snippet")
    def test_process_warning_missing_rule(
        self, mock_extract, mock_ollama, test_args, mock_rules, capture_logs
    ):
        """Test warning processing with missing rule"""
        warning = {"id": 999, "rule_id": 999, "file": "test.py", "line": 10}
        rules_dict = {rule["rule_id"]: rule for rule in mock_rules}

        result = process_warning(warning, rules_dict, "/workspace", test_args)

        assert result is None
        mock_extract.assert_not_called()
        mock_ollama.assert_not_called()

    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.build_prompt")
    @patch("src.main.extract_code_snippet")
    def test_process_warning_ollama_error(
        self, mock_extract, mock_build, mock_ollama, test_args, mock_rules
    ):
        """Test warning processing with Ollama error"""
        mock_extract.return_value = "import unused"
        mock_build.return_value = "test prompt"
        mock_ollama.side_effect = Exception("Ollama connection failed")

        warning = {"id": 0, "rule_id": 0, "file": "test.py", "line": 10}
        rules_dict = {rule["rule_id"]: rule for rule in mock_rules}

        result = process_warning(warning, rules_dict, "/workspace", test_args)

        assert result is None

    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.build_prompt")
    @patch("src.main.extract_code_snippet")
    def test_process_warning_invalid_json_response(
        self, mock_extract, mock_build, mock_ollama, test_args, mock_rules
    ):
        """Test warning processing with invalid JSON response"""
        mock_extract.return_value = "import unused"
        mock_build.return_value = "test prompt"
        mock_ollama.return_value = "Not valid JSON"

        warning = {"id": 0, "rule_id": 0, "file": "test.py", "line": 10}
        rules_dict = {rule["rule_id"]: rule for rule in mock_rules}

        result = process_warning(warning, rules_dict, "/workspace", test_args)

        assert result is None


class TestParseArguments:
    """Test command line argument parsing"""

    @patch.dict("os.environ", {}, clear=True)
    def test_parse_arguments_required(self):
        """Test parsing with required arguments"""
        with patch("sys.argv", ["main.py", "--scan-id", "test-123"]):
            args = parse_arguments()
            assert args.scan_id == "test-123"
            assert args.host == "http://localhost:11434"
            assert args.model == "llama3.1:latest"
            assert args.stream is False
            assert args.verbose is False

    def test_parse_arguments_all_options(self):
        """Test parsing with all options"""
        with patch(
            "sys.argv",
            [
                "main.py",
                "--scan-id",
                "test-456",
                "--host",
                "http://custom:11434",
                "--model",
                "mistral:latest",
                "--stream",
                "--verbose",
            ],
        ):
            args = parse_arguments()
            assert args.scan_id == "test-456"
            assert args.host == "http://custom:11434"
            assert args.model == "mistral:latest"
            assert args.stream is True
            assert args.verbose is True

    @patch.dict(
        "os.environ",
        {"OLLAMA_HOST": "http://env-host:11434", "OLLAMA_MODEL": "env-model"},
    )
    def test_parse_arguments_env_defaults(self):
        """Test that environment variables are used as defaults"""
        with patch("sys.argv", ["main.py", "--scan-id", "test-789"]):
            args = parse_arguments()
            assert args.host == "http://env-host:11434"
            assert args.model == "env-model"

    def test_parse_arguments_missing_scan_id(self):
        """Test that missing scan-id causes error"""
        with patch("sys.argv", ["main.py"]):
            with pytest.raises(SystemExit):
                parse_arguments()


class TestSetupLogging:
    """Test logging configuration"""

    @patch("logging.basicConfig")
    def test_setup_logging_verbose(self, mock_config):
        """Test verbose logging setup"""
        setup_logging(verbose=True)
        mock_config.assert_called_once_with(
            level=10, format="[%(levelname)s] %(message)s"  # logging.DEBUG
        )

    @patch("logging.basicConfig")
    def test_setup_logging_quiet(self, mock_config):
        """Test quiet logging setup"""
        setup_logging(verbose=False)
        mock_config.assert_called_once_with(
            level=30, format="[%(levelname)s] %(message)s"  # logging.WARNING
        )


class TestLogStartupInfo:
    """Test startup logging"""

    @patch("logging.info")
    def test_log_startup_info_verbose(self, mock_log, test_args):
        """Test startup logging in verbose mode"""
        test_args.verbose = True
        log_startup_info(test_args)

        calls = mock_log.call_args_list
        assert len(calls) == 3
        assert "test-scan-123" in str(calls[0])
        assert "localhost:11434" in str(calls[1])
        assert "llama3.1:latest" in str(calls[2])

    @patch("logging.info")
    def test_log_startup_info_quiet(self, mock_log, test_args):
        """Test no startup logging in quiet mode"""
        test_args.verbose = False
        log_startup_info(test_args)
        mock_log.assert_not_called()


class TestMainFunction:
    """Test main function integration"""

    @patch("src.main.get_analysis_data")
    @patch("src.main.parse_arguments")
    @patch("src.main.setup_logging")
    @patch("src.main.log_startup_info")
    @patch("builtins.print")
    def test_main_no_warnings(
        self,
        mock_print,
        mock_log_info,
        mock_setup,
        mock_parse,
        mock_get_data,
        test_args,
    ):
        """Test main function with no warnings"""
        mock_parse.return_value = test_args
        mock_get_data.return_value = ([], [], "/workspace")

        main()

        mock_setup.assert_called_once_with(False)
        mock_log_info.assert_called_once_with(test_args)
        mock_print.assert_called_once()

        # Check that empty JSON array was printed
        printed = mock_print.call_args[0][0]
        assert json.loads(printed) == []

    @patch("src.main.get_analysis_data")
    @patch("src.main.process_warning")
    @patch("src.main.parse_arguments")
    @patch("src.main.setup_logging")
    @patch("src.main.log_startup_info")
    @patch("builtins.print")
    def test_main_with_warnings(
        self,
        mock_print,
        mock_log_info,
        mock_setup,
        mock_parse,
        mock_process,
        mock_get_data,
        test_args,
        mock_warnings,
        mock_rules,
    ):
        """Test main function with warnings"""
        mock_parse.return_value = test_args
        mock_get_data.return_value = (mock_warnings, mock_rules, "/workspace")

        # Mock process_warning to return results for first and third warnings
        mock_process.side_effect = [
            {"warning_id": 0, "original": "import unused", "fixed": ""},
            None,  # Second warning fails
            {"warning_id": 2, "original": "print(x)", "fixed": "logger.info(x)"},
        ]

        main()

        # Check process_warning was called for each warning
        assert mock_process.call_count == 3

        # Check output
        mock_print.assert_called_once()
        printed = mock_print.call_args[0][0]
        results = json.loads(printed)

        assert len(results) == 2
        assert results[0]["warning_id"] == 0
        assert results[1]["warning_id"] == 2

    @patch("src.main.get_analysis_data")
    @patch("src.main.parse_arguments")
    @patch("src.main.setup_logging")
    @patch("src.main.log_startup_info")
    @patch("logging.warning")
    @patch("builtins.print")
    def test_main_verbose_no_warnings(
        self,
        mock_print,
        mock_log_warn,
        mock_log_info,
        mock_setup,
        mock_parse,
        mock_get_data,
    ):
        """Test main function in verbose mode with no warnings"""
        test_args = Mock()
        test_args.verbose = True
        test_args.scan_id = "test-123"

        mock_parse.return_value = test_args
        mock_get_data.return_value = ([], [], "/workspace")

        main()

        mock_log_warn.assert_called_once()
        assert "Aucun warning trouvé" in mock_log_warn.call_args[0][0]

    @patch("src.main.get_analysis_data")
    @patch("src.main.process_warning")
    @patch("src.main.parse_arguments")
    @patch("src.main.setup_logging")
    @patch("src.main.log_startup_info")
    @patch("logging.info")
    @patch("builtins.print")
    def test_main_verbose_with_warnings(
        self,
        mock_print,
        mock_log_info,
        mock_log_startup,
        mock_setup,
        mock_parse,
        mock_process,
        mock_get_data,
        mock_warnings,
        mock_rules,
    ):
        """Test main function in verbose mode with warnings"""
        test_args = Mock()
        test_args.verbose = True
        test_args.scan_id = "test-123"
        test_args.host = "http://localhost:11434"
        test_args.model = "llama3.1:latest"

        mock_parse.return_value = test_args
        mock_get_data.return_value = (mock_warnings, mock_rules, "/workspace")
        mock_process.return_value = {
            "warning_id": 0,
            "original": "test",
            "fixed": "fixed",
        }

        main()

        # Check verbose logging was called
        log_calls = [call[0][0] for call in mock_log_info.call_args_list]
        assert any("3 warnings" in str(call) for call in log_calls)

    @patch("src.main.load_dotenv")
    @patch("src.main.get_analysis_data")
    @patch("src.main.parse_arguments")
    def test_main_loads_dotenv(self, mock_parse, mock_get_data, mock_dotenv):
        """Test that main loads .env file"""
        mock_parse.return_value = Mock(verbose=False, scan_id="test")
        mock_get_data.return_value = ([], [], "/workspace")

        with patch("builtins.print"):
            main()

        mock_dotenv.assert_called_once()


class TestEndToEnd:
    """End-to-end integration tests"""

    @patch("src.main.get_analysis_data")
    @patch("src.main.send_prompt_to_ollama")
    @patch("src.main.extract_code_snippet")
    @patch("sys.argv", ["main.py", "--scan-id", "test-e2e"])
    def test_complete_flow(
        self,
        mock_extract,
        mock_ollama,
        mock_get_data,
        mock_warnings,
        mock_rules,
        capsys,
    ):
        """Test complete flow from arguments to output"""
        # Setup mocks
        mock_get_data.return_value = (
            [mock_warnings[0]],  # Just one warning
            mock_rules,
            "/workspace",
        )
        mock_extract.return_value = "import unused_module"
        mock_ollama.return_value = '{"original": "import unused_module", "fixed": ""}'

        # Run main
        main()

        # Check output
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert len(output) == 1
        assert output[0]["warning_id"] == 0
        assert output[0]["original"] == "import unused_module"
        assert output[0]["fixed"] == ""
