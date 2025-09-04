"""
Unit tests for the API issues module
"""

import os
from unittest.mock import Mock, patch

import pytest
import requests

from src.api.issues import extract_repo_name_from_url, get_analysis_data


class TestExtractRepoNameFromUrl:
    """Test repository name extraction from URLs"""

    def test_extract_github_url(self):
        """Test extracting repo name from GitHub URL"""
        url = "https://github.com/organization/repository-name"
        result = extract_repo_name_from_url(url)
        assert result == "repository-name"

    def test_extract_github_url_with_git_extension(self):
        """Test extracting repo name from GitHub URL with .git"""
        url = "https://github.com/user/my-repo.git"
        result = extract_repo_name_from_url(url)
        assert result == "my-repo"

    def test_extract_gitlab_url(self):
        """Test extracting repo name from GitLab URL"""
        url = "https://gitlab.com/group/subgroup/project-name"
        result = extract_repo_name_from_url(url)
        assert result == "project-name"

    def test_extract_ssh_url(self):
        """Test extracting repo name from SSH URL"""
        url = "git@github.com:organization/repo-name.git"
        result = extract_repo_name_from_url(url)
        assert result == "repo-name"

    def test_extract_custom_git_url(self):
        """Test extracting repo name from custom Git URL"""
        url = "https://git.company.com/team/project.git"
        result = extract_repo_name_from_url(url)
        assert result == "project"

    def test_extract_url_with_trailing_slash(self):
        """Test extracting repo name with trailing slash"""
        url = "https://github.com/org/repo/"
        result = extract_repo_name_from_url(url)
        assert result == "repo"

    def test_extract_empty_url(self):
        """Test handling empty URL"""
        result = extract_repo_name_from_url("")
        assert result is None

    def test_extract_none_url(self):
        """Test handling None URL"""
        result = extract_repo_name_from_url(None)
        assert result is None

    def test_extract_invalid_url(self):
        """Test handling invalid URL"""
        url = "not-a-valid-url"
        result = extract_repo_name_from_url(url)
        # Should still attempt to extract something
        assert result == "not-a-valid-url"

    def test_extract_url_no_path(self):
        """Test URL with no path"""
        url = "https://github.com"
        result = extract_repo_name_from_url(url)
        assert result == ""


class TestGetAnalysisData:
    """Test fetching analysis data from API"""

    @patch("requests.get")
    def test_get_analysis_data_success(self, mock_get, mock_api_response):
        """Test successful API data retrieval"""
        # Setup mock response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_api_response
        mock_get.return_value = mock_resp

        # Call function
        warnings, rules, workspace = get_analysis_data("test-scan-123")

        # Assertions
        assert warnings == mock_api_response["analysis"]["warnings"]
        assert rules == mock_api_response["rules"]
        assert workspace == "repo"  # Extracted from repo_url

        # Check API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "test-scan-123" in call_args[0][0]

    @patch("requests.get")
    def test_get_analysis_data_with_workspace_path(self, mock_get, mock_api_response):
        """Test API data retrieval with workspace_path in response"""
        # Add workspace_path to response
        mock_api_response["analysis"]["workspace_path"] = "/custom/workspace"

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_api_response
        mock_get.return_value = mock_resp

        warnings, rules, workspace = get_analysis_data("test-scan-456")

        assert workspace == "/custom/workspace"

    @patch("requests.get")
    def test_get_analysis_data_no_repo_url(self, mock_get, mock_api_response):
        """Test API data retrieval without repo_url"""
        # Remove repo_url
        mock_api_response["analysis"].pop("repo_url")

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_api_response
        mock_get.return_value = mock_resp

        warnings, rules, workspace = get_analysis_data("test-scan-789")

        assert workspace is None

    @patch("requests.get")
    def test_get_analysis_data_http_error(self, mock_get):
        """Test handling of HTTP errors"""
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = requests.HTTPError("Not Found")
        mock_get.return_value = mock_resp

        warnings, rules, workspace = get_analysis_data("invalid-scan")

        assert warnings == []
        assert rules == []
        assert workspace is None

    @patch("requests.get")
    def test_get_analysis_data_connection_error(self, mock_get):
        """Test handling of connection errors"""
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        warnings, rules, workspace = get_analysis_data("test-scan")

        assert warnings == []
        assert rules == []
        assert workspace is None

    @patch("requests.get")
    def test_get_analysis_data_timeout(self, mock_get):
        """Test handling of timeout errors"""
        mock_get.side_effect = requests.Timeout("Request timeout")

        warnings, rules, workspace = get_analysis_data("test-scan")

        assert warnings == []
        assert rules == []
        assert workspace is None

    @patch("requests.get")
    def test_get_analysis_data_json_error(self, mock_get):
        """Test handling of invalid JSON response"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_resp

        warnings, rules, workspace = get_analysis_data("test-scan")

        assert warnings == []
        assert rules == []
        assert workspace is None

    @patch("requests.get")
    def test_get_analysis_data_missing_fields(self, mock_get):
        """Test handling of response with missing fields"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "analysis": {
                # Missing warnings field
                "repo_url": "https://github.com/test/repo"
            },
            # Missing rules field entirely
        }
        mock_get.return_value = mock_resp

        warnings, rules, workspace = get_analysis_data("test-scan")

        # Should handle missing fields gracefully
        assert warnings == []
        assert rules == []
        assert workspace == "repo"

    @patch("requests.get")
    @patch.dict(os.environ, {"API_BASE_URL": "http://custom-api:9000/api"})
    def test_get_analysis_data_custom_api_url(self, mock_get, mock_api_response):
        """Test using custom API URL from environment"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_api_response
        mock_get.return_value = mock_resp

        get_analysis_data("test-scan")

        # Check custom API URL was used
        call_url = mock_get.call_args[0][0]
        assert "http://custom-api:9000/api" in call_url

    @patch("requests.get")
    def test_get_analysis_data_empty_warnings(self, mock_get):
        """Test handling of empty warnings list"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "analysis": {"warnings": [], "repo_url": "https://github.com/test/repo"},
            "rules": [],
        }
        mock_get.return_value = mock_resp

        warnings, rules, workspace = get_analysis_data("test-scan")

        assert warnings == []
        assert rules == []
        assert workspace == "repo"

    @patch("requests.get")
    @patch("logging.error")
    def test_get_analysis_data_logs_errors(self, mock_log, mock_get):
        """Test that errors are properly logged"""
        mock_get.side_effect = Exception("Unexpected error")

        warnings, rules, workspace = get_analysis_data("test-scan")

        # Check error was logged
        mock_log.assert_called()
        assert "Unexpected error" in str(mock_log.call_args)

    @patch("requests.get")
    def test_get_analysis_data_partial_response(self, mock_get):
        """Test handling of partial API response"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "analysis": {
                "warnings": [{"id": 1, "rule_id": 1, "file": "test.py", "line": 10}],
                # repo_url missing
            },
            "rules": [{"rule_id": 1, "name": "Test Rule"}],
        }
        mock_get.return_value = mock_resp

        warnings, rules, workspace = get_analysis_data("test-scan")

        assert len(warnings) == 1
        assert len(rules) == 1
        assert workspace is None


class TestIntegrationWithEnvironment:
    """Integration tests with environment variables"""

    @patch("requests.get")
    def test_full_flow_with_env_vars(self, mock_get, mock_api_response, monkeypatch):
        """Test complete flow with environment variables set"""
        # Set environment variables
        monkeypatch.setenv("API_BASE_URL", "http://test-api:8080/api")

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_api_response
        mock_get.return_value = mock_resp

        warnings, rules, workspace = get_analysis_data("env-test-scan")

        # Verify all data extracted correctly
        assert len(warnings) == 3
        assert len(rules) == 2
        assert workspace == "repo"

        # Verify correct API endpoint used
        call_url = mock_get.call_args[0][0]
        assert "http://test-api:8080/api" in call_url
        assert "env-test-scan" in call_url
