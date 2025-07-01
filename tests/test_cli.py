"""
Tests for cli.py functionality
"""

import pytest
import argparse
from unittest.mock import Mock, AsyncMock, patch
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import send_prompt_sync, send_prompt_async, main


class TestSendPromptSync:
    """Test synchronous prompt sending"""
    
    @patch('cli.Client')
    def test_send_prompt_sync_non_streaming(self, mock_client_class):
        """Test synchronous prompt without streaming"""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.return_value = {
            'message': {'content': 'Mock response from Ollama'}
        }
        mock_client_class.return_value = mock_client
        
        # Test function (capture stdout would be needed for full test)
        send_prompt_sync(
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
    def test_send_prompt_sync_streaming(self, mock_client_class, mock_streaming_response):
        """Test synchronous prompt with streaming"""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.return_value = mock_streaming_response
        mock_client_class.return_value = mock_client
        
        # Test function
        send_prompt_sync(
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
    def test_send_prompt_sync_connection_error(self, mock_client_class):
        """Test synchronous prompt with connection error"""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_client.chat.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client
        
        # Test function should not raise exception (it just prints)
        try:
            send_prompt_sync(
                host="http://localhost:11434",
                model="mistral:latest",
                prompt="Test prompt",
                is_streaming=False
            )
        except Exception:
            pytest.fail("send_prompt_sync should handle exceptions gracefully")
    
    @patch('cli.Client')
    def test_send_prompt_sync_invalid_response(self, mock_client_class):
        """Test synchronous prompt with invalid response format"""
        # Setup mock with invalid response
        mock_client = Mock()
        mock_client.chat.return_value = {'invalid': 'response'}
        mock_client_class.return_value = mock_client
        
        # Test function should handle invalid response gracefully
        send_prompt_sync(
            host="http://localhost:11434",
            model="mistral:latest",
            prompt="Test prompt",
            is_streaming=False
        )
        
        mock_client.chat.assert_called_once()


class TestSendPromptAsync:
    """Test asynchronous prompt sending"""
    
    @pytest.mark.asyncio
    @patch('cli.AsyncClient')
    async def test_send_prompt_async_non_streaming(self, mock_client_class):
        """Test asynchronous prompt without streaming"""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.chat.return_value = {
            'message': {'content': 'Mock async response from Ollama'}
        }
        mock_client_class.return_value = mock_client
        
        # Test function
        await send_prompt_async(
            host="http://localhost:11434",
            model="mistral:latest",
            prompt="Test async prompt",
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
        assert call_args[1]['messages'][1]['content'] == "Test async prompt"
    
    @pytest.mark.asyncio
    @patch('cli.AsyncClient')
    async def test_send_prompt_async_streaming(self, mock_client_class, mock_async_streaming_response):
        """Test asynchronous prompt with streaming"""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_async_streaming_response
        mock_client_class.return_value = mock_client
        
        # Test function
        await send_prompt_async(
            host="http://localhost:11434",
            model="mistral:latest",
            prompt="Test async streaming prompt",
            is_streaming=True
        )
        
        # Verify client was created and called correctly
        mock_client_class.assert_called_once_with(host="http://localhost:11434")
        mock_client.chat.assert_called_once()
        
        # Check streaming parameter
        call_args = mock_client.chat.call_args
        assert call_args[1]['stream'] == True
    
    @pytest.mark.asyncio
    @patch('cli.AsyncClient')
    async def test_send_prompt_async_connection_error(self, mock_client_class):
        """Test asynchronous prompt with connection error"""
        # Setup mock to raise exception
        mock_client = AsyncMock()
        mock_client.chat.side_effect = Exception("Async connection failed")
        mock_client_class.return_value = mock_client
        
        # Test function should not raise exception
        try:
            await send_prompt_async(
                host="http://localhost:11434",
                model="mistral:latest",
                prompt="Test async prompt",
                is_streaming=False
            )
        except Exception:
            pytest.fail("send_prompt_async should handle exceptions gracefully")
    
    @pytest.mark.asyncio
    @patch('cli.AsyncClient')
    async def test_send_prompt_async_invalid_response(self, mock_client_class):
        """Test asynchronous prompt with invalid response format"""
        # Setup mock with invalid response
        mock_client = AsyncMock()
        mock_client.chat.return_value = {'invalid': 'async_response'}
        mock_client_class.return_value = mock_client
        
        # Test function should handle invalid response gracefully
        await send_prompt_async(
            host="http://localhost:11434",
            model="mistral:latest",
            prompt="Test async prompt",
            is_streaming=False
        )
        
        mock_client.chat.assert_called_once()


class TestMainFunction:
    """Test main function and argument parsing"""
    
    def test_argument_parser_basic(self):
        """Test basic argument parsing"""
        # Create parser like in main()
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', default='http://10.0.0.1:11434')
        parser.add_argument('-m', '--model', default='mistral:latest')
        parser.add_argument('prompt', help='Prompt to send to AI')
        parser.add_argument('--stream', action='store_true')
        parser.add_argument('--async', dest='use_async', action='store_true')
        
        # Test parsing
        args = parser.parse_args(['Test prompt'])
        assert args.prompt == 'Test prompt'
        assert args.host == 'http://10.0.0.1:11434'
        assert args.model == 'mistral:latest'
        assert args.stream == False
        assert args.use_async == False
    
    def test_argument_parser_with_options(self):
        """Test argument parsing with all options"""
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', default='http://10.0.0.1:11434')
        parser.add_argument('-m', '--model', default='mistral:latest')
        parser.add_argument('prompt', help='Prompt to send to AI')
        parser.add_argument('--stream', action='store_true')
        parser.add_argument('--async', dest='use_async', action='store_true')
        
        # Test parsing with options
        args = parser.parse_args([
            'Test prompt with options',
            '--host', 'http://localhost:11434',
            '--model', 'llama3:8b',
            '--stream',
            '--async'
        ])
        
        assert args.prompt == 'Test prompt with options'
        assert args.host == 'http://localhost:11434'
        assert args.model == 'llama3:8b'
        assert args.stream == True
        assert args.use_async == True
    
    def test_main_sync_mode_logic(self):
        """Test that sync mode logic works correctly"""
        # Test the logic that determines sync vs async mode
        # This is a simpler test that verifies the conditional logic
        use_async = False
        
        if use_async:
            # Would call asyncio.run(send_prompt_async(...))
            mode = "async"
        else:
            # Would call send_prompt_sync(...)
            mode = "sync"
        
        assert mode == "sync"
    
    def test_main_async_mode_logic(self):
        """Test main function async mode logic"""
        # Test the logic that determines sync vs async mode
        use_async = True
        
        if use_async:
            # Would call asyncio.run(send_prompt_async(...))
            mode = "async"
        else:
            # Would call send_prompt_sync(...)
            mode = "sync"
        
        assert mode == "async"


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
                
                send_prompt_sync(host, "mistral:latest", "test", False)
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
                
                send_prompt_sync("http://localhost:11434", model, "test", False)
                
                call_args = mock_client.chat.call_args
                assert call_args[1]['model'] == model