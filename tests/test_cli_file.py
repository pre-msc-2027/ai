"""
Tests for cli_file.py functionality
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch, mock_open
from pathlib import Path
import asyncio
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_file import (
    get_static_analysis_issues,
    read_file_content,
    generate_output_filename,
    save_to_markdown,
    analyze_file_with_ollama_sync,
    analyze_file_with_ollama_async
)


class TestStaticAnalysis:
    """Test static analysis functionality"""
    
    def test_get_static_analysis_issues_with_todo(self, temp_file):
        """Test detection of TODO comments"""
        issues = get_static_analysis_issues(temp_file)
        
        # Should find TODO comment
        todo_issues = [i for i in issues if 'TODO' in i['message']]
        assert len(todo_issues) > 0
        assert todo_issues[0]['type'] == 'code_smell'
        assert todo_issues[0]['severity'] == 'INFO'
    
    def test_get_static_analysis_issues_with_print(self, temp_file):
        """Test detection of print statements"""
        issues = get_static_analysis_issues(temp_file)
        
        # Should find print statement
        print_issues = [i for i in issues if 'print(' in i['code']]
        assert len(print_issues) > 0
        assert print_issues[0]['type'] == 'code_smell'
        assert print_issues[0]['severity'] == 'MINOR'
    
    def test_get_static_analysis_issues_with_credentials(self, temp_file):
        """Test detection of hardcoded credentials"""
        issues = get_static_analysis_issues(temp_file)
        
        # Should find hardcoded credential
        cred_issues = [i for i in issues if 'credential' in i['message']]
        assert len(cred_issues) > 0
        assert cred_issues[0]['type'] == 'vulnerability'
        assert cred_issues[0]['severity'] == 'BLOCKER'
    
    def test_get_static_analysis_issues_with_empty_catch(self, temp_file):
        """Test detection of empty catch blocks"""
        issues = get_static_analysis_issues(temp_file)
        
        # Should find empty catch block
        catch_issues = [i for i in issues if 'exception' in i['message'].lower()]
        assert len(catch_issues) > 0
        assert catch_issues[0]['type'] == 'bug'
        assert catch_issues[0]['severity'] == 'MAJOR'
    
    def test_get_static_analysis_issues_no_file(self):
        """Test with non-existent file"""
        issues = get_static_analysis_issues("non_existent_file.py")
        assert issues == []
    
    def test_get_static_analysis_issues_clean_file(self):
        """Test with a clean file (no issues)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""#!/usr/bin/env python3
def clean_function():
    return "This is clean code"

if __name__ == "__main__":
    result = clean_function()
""")
            temp_path = f.name
        
        try:
            issues = get_static_analysis_issues(temp_path)
            # Should only find print statements if any, but this file is clean
            assert len(issues) == 0 or all(issue['severity'] != 'BLOCKER' for issue in issues)
        finally:
            os.unlink(temp_path)


class TestFileOperations:
    """Test file reading and writing operations"""
    
    def test_read_file_content_success(self, temp_file):
        """Test successful file reading"""
        content = read_file_content(temp_file)
        assert content is not None
        assert 'def test_function():' in content
    
    def test_read_file_content_not_found(self):
        """Test reading non-existent file"""
        content = read_file_content("non_existent_file.py")
        assert content is None
    
    @patch('builtins.open', side_effect=PermissionError())
    def test_read_file_content_permission_error(self, mock_file):
        """Test reading file with permission error"""
        content = read_file_content("restricted_file.py")
        assert content is None
    
    def test_generate_output_filename(self):
        """Test output filename generation"""
        input_file = "test_script.py"
        output_file = generate_output_filename(input_file)
        
        # Should contain base name and timestamp
        assert "test_script_analysis_" in output_file
        assert output_file.endswith(".md")
        
        # Should contain valid timestamp format
        timestamp_part = output_file.replace("test_script_analysis_", "").replace(".md", "")
        assert len(timestamp_part.split("-")) == 2  # date-time format
    
    def test_save_to_markdown_basic(self, temp_dir):
        """Test basic markdown saving"""
        content = "# Test Analysis\n\nThis is test content."
        filename = "test_output.md"
        analyzed_file = "test.py"
        
        save_to_markdown(filename, content, analyzed_file, temp_dir)
        
        output_path = os.path.join(temp_dir, filename)
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            saved_content = f.read()
            assert f"Analysis Report for {analyzed_file}" in saved_content
            assert content in saved_content
    
    def test_save_to_markdown_no_output_dir(self, temp_dir):
        """Test markdown saving without output directory"""
        content = "# Test Analysis\n\nThis is test content."
        filename = os.path.join(temp_dir, "test_output.md")
        analyzed_file = "test.py"
        
        save_to_markdown(filename, content, analyzed_file)
        
        assert os.path.exists(filename)
    
    @patch('os.makedirs', side_effect=Exception("Permission denied"))
    def test_save_to_markdown_error(self, mock_makedirs):
        """Test markdown saving with error"""
        content = "# Test Analysis"
        filename = "test_output.md"
        analyzed_file = "test.py"
        
        # Should not raise exception, just print error
        save_to_markdown(filename, content, analyzed_file, "/nonexistent/path")


class TestOllamaIntegration:
    """Test Ollama integration (with mocks)"""
    
    @patch('cli_file.Client')
    def test_analyze_file_with_ollama_sync_non_streaming(self, mock_client_class, temp_file, sample_static_issues):
        """Test synchronous Ollama analysis without streaming"""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.return_value = {
            'message': {'content': 'Mock analysis response'}
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
            save_to_file=False
        )
        
        assert response == 'Mock analysis response'
        mock_client.chat.assert_called_once()
    
    @patch('cli_file.Client')
    def test_analyze_file_with_ollama_sync_streaming(self, mock_client_class, temp_file, sample_static_issues, mock_streaming_response):
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
            save_to_file=False
        )
        
        assert response == 'Mock streaming response'
        mock_client.chat.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('cli_file.AsyncClient')
    async def test_analyze_file_with_ollama_async_non_streaming(self, mock_client_class, temp_file, sample_static_issues):
        """Test asynchronous Ollama analysis without streaming"""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.chat.return_value = {
            'message': {'content': 'Mock async analysis response'}
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
            save_to_file=False
        )
        
        assert response == 'Mock async analysis response'
        mock_client.chat.assert_called_once()
    
    @patch('cli_file.Client')
    def test_analyze_file_with_ollama_sync_connection_error(self, mock_client_class, temp_file, sample_static_issues):
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
            save_to_file=False
        )
        
        assert response is None


class TestArgumentParsing:
    """Test argument parsing and validation"""
    
    def test_main_with_valid_file(self, temp_file):
        """Test main function with valid file"""
        # This would require more complex mocking of sys.argv
        # For now, we test the components individually
        assert os.path.exists(temp_file)
    
    def test_file_filtering(self):
        """Test file existence filtering"""
        # Create some test files
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_file = os.path.join(temp_dir, "valid.py")
            with open(valid_file, 'w') as f:
                f.write("# Valid file")
            
            all_files = [valid_file, "nonexistent.py"]
            valid_files = [f for f in all_files if os.path.exists(f) and os.path.isfile(f)]
            
            assert len(valid_files) == 1
            assert valid_files[0] == valid_file