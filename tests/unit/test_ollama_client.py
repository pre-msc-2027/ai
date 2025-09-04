"""
Unit tests for the Ollama client module
"""

from unittest.mock import Mock, patch

import pytest

from src.ollama.client import send_prompt_to_ollama


class TestSendPromptToOllama:
    """Test Ollama client functionality"""

    @patch("ollama.Client")
    def test_send_prompt_success(self, mock_client_class):
        """Test successful prompt sending"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {"message": {"content": "AI response content"}}

        # Call function
        result = send_prompt_to_ollama(
            prompt="Test prompt", model="llama3.1:latest", host="http://localhost:11434"
        )

        # Assertions
        assert result == "AI response content"
        mock_client_class.assert_called_once_with(host="http://localhost:11434")
        mock_client.chat.assert_called_once_with(
            model="llama3.1:latest",
            messages=[{"role": "user", "content": "Test prompt"}],
        )

    @patch("ollama.Client")
    def test_send_prompt_with_json_response(self, mock_client_class):
        """Test sending prompt that returns JSON"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {"content": '{"original": "test", "fixed": "fixed"}'}
        }

        result = send_prompt_to_ollama(
            prompt="Fix this code", model="mistral:latest", host="http://custom:11434"
        )

        assert result == '{"original": "test", "fixed": "fixed"}'
        mock_client_class.assert_called_once_with(host="http://custom:11434")

    @patch("ollama.Client")
    @patch("logging.error")
    def test_send_prompt_connection_error(self, mock_log, mock_client_class):
        """Test handling of connection errors"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.side_effect = ConnectionError("Connection refused")

        result = send_prompt_to_ollama(
            prompt="Test prompt", model="llama3.1:latest", host="http://localhost:11434"
        )

        assert result == "Erreur lors de la génération de la réponse IA."
        mock_log.assert_called_once()
        assert "Connection refused" in str(mock_log.call_args)

    @patch("ollama.Client")
    @patch("logging.error")
    def test_send_prompt_model_not_found(self, mock_log, mock_client_class):
        """Test handling of model not found error"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.side_effect = Exception("model 'unknown:latest' not found")

        result = send_prompt_to_ollama(
            prompt="Test prompt", model="unknown:latest", host="http://localhost:11434"
        )

        assert result == "Erreur lors de la génération de la réponse IA."
        mock_log.assert_called_once()
        assert "unknown:latest" in str(mock_log.call_args)

    @patch("ollama.Client")
    @patch("logging.error")
    def test_send_prompt_timeout(self, mock_log, mock_client_class):
        """Test handling of timeout errors"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.side_effect = TimeoutError("Request timeout")

        result = send_prompt_to_ollama(
            prompt="Test prompt", model="llama3.1:latest", host="http://localhost:11434"
        )

        assert result == "Erreur lors de la génération de la réponse IA."
        mock_log.assert_called_once()
        assert "Request timeout" in str(mock_log.call_args)

    @patch("ollama.Client")
    @patch("logging.error")
    def test_send_prompt_invalid_response(self, mock_log, mock_client_class):
        """Test handling of invalid response structure"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        # Return invalid structure (missing 'message' key)
        mock_client.chat.return_value = {"error": "Invalid request"}

        result = send_prompt_to_ollama(
            prompt="Test prompt", model="llama3.1:latest", host="http://localhost:11434"
        )

        assert result == "Erreur lors de la génération de la réponse IA."
        mock_log.assert_called_once()

    @patch("ollama.Client")
    def test_send_prompt_empty_response(self, mock_client_class):
        """Test handling of empty response content"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {"message": {"content": ""}}

        result = send_prompt_to_ollama(
            prompt="Test prompt", model="llama3.1:latest", host="http://localhost:11434"
        )

        assert result == ""

    @patch("ollama.Client")
    def test_send_prompt_multiline_response(self, mock_client_class):
        """Test handling of multiline responses"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        multiline_content = """Line 1
Line 2
{"original": "code", "fixed": "fixed_code"}
Line 4"""
        mock_client.chat.return_value = {"message": {"content": multiline_content}}

        result = send_prompt_to_ollama(
            prompt="Test prompt", model="llama3.1:latest", host="http://localhost:11434"
        )

        assert result == multiline_content
        assert '{"original": "code", "fixed": "fixed_code"}' in result

    @patch("ollama.Client")
    def test_send_prompt_with_special_characters(self, mock_client_class):
        """Test sending prompt with special characters"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {"content": "Response with émojis 🤖 and spéçiäl chars"}
        }

        prompt_with_special = "Prompt with\nnewlines\tand émojis 🐍"
        result = send_prompt_to_ollama(
            prompt=prompt_with_special,
            model="llama3.1:latest",
            host="http://localhost:11434",
        )

        assert "émojis 🤖" in result
        # Check the prompt was sent correctly
        sent_prompt = mock_client.chat.call_args[1]["messages"][0]["content"]
        assert sent_prompt == prompt_with_special

    @patch("ollama.Client")
    def test_send_prompt_different_hosts(self, mock_client_class):
        """Test that different hosts create different clients"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {"message": {"content": "response"}}

        # Call with different hosts
        hosts = [
            "http://localhost:11434",
            "http://192.168.1.100:11434",
            "http://ollama.local:11434",
        ]

        for host in hosts:
            send_prompt_to_ollama("prompt", "model", host)

        # Check each host was used
        assert mock_client_class.call_count == len(hosts)
        for i, host in enumerate(hosts):
            assert mock_client_class.call_args_list[i][1]["host"] == host

    @patch("ollama.Client")
    @patch("logging.error")
    def test_send_prompt_generic_exception(self, mock_log, mock_client_class):
        """Test handling of generic exceptions"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat.side_effect = Exception("Unexpected error")

        result = send_prompt_to_ollama(
            prompt="Test", model="model", host="http://localhost:11434"
        )

        assert result == "Erreur lors de la génération de la réponse IA."
        mock_log.assert_called_once()
        assert "Unexpected error" in str(mock_log.call_args[0][0])
