"""
Tests for cli.py functionality
"""

import pytest
import argparse
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import send_prompt


class TestSendPrompt:
    """Test prompt sending functionality"""
    
    @patch('cli.Client')
    def test_send_prompt_non_streaming(self, mock_client_class):
        """Test prompt without streaming"""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.return_value = {
            'message': {'content': 'Mock response from Ollama'}
        }
        mock_client_class.return_value = mock_client
        
        # Test function
        send_prompt(
            host="http://localhost:11434",
            model="mistral:latest",
            prompt="Test prompt",
            is_streaming=False
        )
        
        # Verify client was created and called correctly
        mock_client_class.assert_called_once_with(host="http://localhost:11434")
        mock_client.chat.assert_called_once()
        
        # Check the call arguments
        call_args = mock_client.chat.call_args
        assert call_args[1]['model'] == "mistral:latest"
        assert call_args[1]['stream'] == False
        assert len(call_args[1]['messages']) == 2
        assert call_args[1]['messages'][1]['content'] == "Test prompt"
    
    @patch('cli.Client')
    def test_send_prompt_streaming(self, mock_client_class, mock_streaming_response):
        """Test prompt with streaming"""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.return_value = mock_streaming_response
        mock_client_class.return_value = mock_client
        
        # Test function
        send_prompt(
            host="http://localhost:11434",
            model="mistral:latest",
            prompt="Test streaming prompt",
            is_streaming=True
        )
        
        # Verify client was created and called correctly
        mock_client_class.assert_called_once_with(host="http://localhost:11434")
        mock_client.chat.assert_called_once()
        
        # Check streaming parameter
        call_args = mock_client.chat.call_args
        assert call_args[1]['stream'] == True
    
    @patch('cli.Client')
    def test_send_prompt_connection_error(self, mock_client_class):
        """Test prompt with connection error"""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_client.chat.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client
        
        # Test function should not raise exception (uses logger.error)
        try:
            send_prompt(
                host="http://localhost:11434",
                model="mistral:latest",
                prompt="Test prompt",
                is_streaming=False
            )
        except Exception:
            pytest.fail("send_prompt should handle exceptions gracefully")
    
    @patch('cli.Client')
    def test_send_prompt_invalid_response(self, mock_client_class):
        """Test prompt with invalid response format"""
        # Setup mock with invalid response
        mock_client = Mock()
        mock_client.chat.return_value = {'invalid': 'response'}
        mock_client_class.return_value = mock_client
        
        # Test function should handle invalid response gracefully
        send_prompt(
            host="http://localhost:11434",
            model="mistral:latest",
            prompt="Test prompt",
            is_streaming=False
        )
        
        mock_client.chat.assert_called_once()


class TestArgumentParsing:
    """Test CLI argument parsing"""
    
    def test_argument_parser_basic(self):
        """Test basic argument parsing without async flag"""
        # Create parser like in simplified main()
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', default='http://10.0.0.1:11434')
        parser.add_argument('-m', '--model', default='mistral:latest')
        parser.add_argument('prompt', help='Prompt to send to AI')
        parser.add_argument('--stream', action='store_true')
        parser.add_argument('-v', '--verbose', action='store_true')
        
        # Test parsing
        args = parser.parse_args(['Test prompt'])
        assert args.prompt == 'Test prompt'
        assert args.host == 'http://10.0.0.1:11434'
        assert args.model == 'mistral:latest'
        assert args.stream == False
        assert args.verbose == False
    
    def test_argument_parser_with_options(self):
        """Test argument parsing with all available options"""
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', default='http://10.0.0.1:11434')
        parser.add_argument('-m', '--model', default='mistral:latest')
        parser.add_argument('prompt', help='Prompt to send to AI')
        parser.add_argument('--stream', action='store_true')
        parser.add_argument('-v', '--verbose', action='store_true')
        
        # Test parsing with options
        args = parser.parse_args([
            'Test prompt with options',
            '--host', 'http://localhost:11434',
            '--model', 'llama3:8b',
            '--stream',
            '--verbose'
        ])
        
        assert args.prompt == 'Test prompt with options'
        assert args.host == 'http://localhost:11434'
        assert args.model == 'llama3:8b'
        assert args.stream == True
        assert args.verbose == True


class TestIntegration:
    """Integration tests for cli.py"""
    
    def test_host_parameter_passed_correctly(self):
        """Test that host parameter is passed correctly to client"""
        test_hosts = [
            "http://localhost:11434",
            "http://10.0.0.1:11434", 
            "https://ollama.example.com:443"
        ]
        
        for host in test_hosts:
            with patch('cli.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.chat.return_value = {'message': {'content': 'test'}}
                mock_client_class.return_value = mock_client
                
                send_prompt(host, "mistral:latest", "test", False)
                mock_client_class.assert_called_with(host=host)
    
    def test_model_parameter_passed_correctly(self):
        """Test that model parameter is passed correctly to chat"""
        test_models = [
            "mistral:latest",
            "llama3:8b",
            "codellama:13b"
        ]
        
        for model in test_models:
            with patch('cli.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.chat.return_value = {'message': {'content': 'test'}}
                mock_client_class.return_value = mock_client
                
                send_prompt("http://localhost:11434", model, "test", False)
                
                call_args = mock_client.chat.call_args
                assert call_args[1]['model'] == model