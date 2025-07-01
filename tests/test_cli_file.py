"""
Tests for cli_file.py functionality
"""

import pytest
import os
import tempfile
import logging
from unittest.mock import Mock, patch, mock_open
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
    analyze_file_with_ollama_async,
    # New helper functions
    _create_argument_parser,
    _configure_logging,
    _expand_file_patterns,
    _validate_files,
    _process_multiple_files,
    _process_single_file,
    # New checker functions
    check_todo_comments,
    check_print_statements,
    check_long_lines,
    check_empty_catch_blocks,
    check_hardcoded_credentials,
    check_unused_imports
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
        from unittest.mock import AsyncMock
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


class TestCheckerFunctions:
    """Test individual checker functions for static analysis"""
    
    def test_check_todo_comments_found(self):
        """Test TODO comment detection"""
        result = check_todo_comments("# TODO: Fix this later", 5)
        assert result is not None
        assert result['line'] == 5
        assert result['type'] == 'code_smell'
        assert result['severity'] == 'INFO'
        assert 'TODO' in result['message']
    
    def test_check_todo_comments_not_found(self):
        """Test when no TODO comments"""
        result = check_todo_comments("# Regular comment", 1)
        assert result is None
    
    def test_check_print_statements_python(self):
        """Test print statement detection in Python files"""
        result = check_print_statements("print('Hello world')", 10, "test.py")
        assert result is not None
        assert result['line'] == 10
        assert result['type'] == 'code_smell'
        assert result['severity'] == 'MINOR'
    
    def test_check_print_statements_non_python(self):
        """Test print statement ignored in non-Python files"""
        result = check_print_statements("print('Hello')", 1, "test.js")
        assert result is None
    
    def test_check_long_lines(self):
        """Test long line detection"""
        long_line = "x" * 150  # Create a line longer than 120 chars
        result = check_long_lines(long_line, 3)
        assert result is not None
        assert result['line'] == 3
        assert result['type'] == 'code_smell'
        assert result['severity'] == 'MINOR'
        assert "120 characters" in result['message']
    
    def test_check_long_lines_ok(self):
        """Test short line passes"""
        result = check_long_lines("short line", 1)
        assert result is None
    
    def test_check_hardcoded_credentials(self):
        """Test hardcoded credential detection"""
        result = check_hardcoded_credentials("password='secret123'", 8)
        assert result is not None
        assert result['line'] == 8
        assert result['type'] == 'vulnerability'
        assert result['severity'] == 'BLOCKER'
    
    def test_check_hardcoded_credentials_comment(self):
        """Test credentials in comments are ignored"""
        result = check_hardcoded_credentials("# password='example'", 1)
        assert result is None
    
    def test_check_unused_imports(self):
        """Test unused import detection"""
        content = "import json\nprint('hello')"  # json not used
        result = check_unused_imports("import json", 1, content, "test.py")
        assert result is not None
        assert result['type'] == 'code_smell'
        assert result['severity'] == 'MINOR'
        assert 'json' in result['message']


class TestMainHelperFunctions:
    """Test the new helper functions from main() refactoring"""
    
    def test_create_argument_parser(self):
        """Test argument parser creation"""
        parser = _create_argument_parser()
        
        # Test default values
        args = parser.parse_args(['test.py'])
        assert args.host == 'http://10.0.0.1:11434'
        assert args.model == 'mistral:latest'
        assert args.file == ['test.py']
        assert args.stream == False
        assert args.verbose == False
        assert args.output == False
        assert args.concurrent == 4
    
    def test_create_argument_parser_with_options(self):
        """Test argument parser with all options"""
        parser = _create_argument_parser()
        
        args = parser.parse_args([
            'file1.py', 'file2.py',
            '--host', 'http://localhost:11434', 
            '--model', 'llama3:8b',
            '--stream',
            '--verbose',
            '--output',
            '--concurrent', '8'
        ])
        
        assert args.host == 'http://localhost:11434'
        assert args.model == 'llama3:8b'
        assert args.file == ['file1.py', 'file2.py']
        assert args.stream == True
        assert args.verbose == True
        assert args.output == True
        assert args.concurrent == 8
    
    @patch('cli_file.logging.basicConfig')
    def test_configure_logging_verbose(self, mock_basic_config):
        """Test logging configuration in verbose mode"""
        _configure_logging(True)
        mock_basic_config.assert_called_once()
        
        call_args = mock_basic_config.call_args[1]
        assert call_args['level'] == logging.DEBUG
        assert '[%(asctime)s]' in call_args['format']
    
    @patch('cli_file.logging.basicConfig')
    def test_configure_logging_quiet(self, mock_basic_config):
        """Test logging configuration in quiet mode"""
        _configure_logging(False)
        mock_basic_config.assert_called_once()
        
        call_args = mock_basic_config.call_args[1]
        assert call_args['level'] == logging.WARNING
    
    @patch('glob.glob')
    def test_expand_file_patterns_with_glob(self, mock_glob):
        """Test file pattern expansion with glob matches"""
        mock_glob.return_value = ['file1.py', 'file2.py']
        
        result = _expand_file_patterns(['src/*.py'])
        
        mock_glob.assert_called_once_with('src/*.py')
        assert result == ['file1.py', 'file2.py']
    
    @patch('glob.glob')
    def test_expand_file_patterns_no_glob(self, mock_glob):
        """Test file pattern expansion without glob matches"""
        mock_glob.return_value = []
        
        result = _expand_file_patterns(['specific_file.py'])
        
        assert result == ['specific_file.py']
    
    @patch('glob.glob')
    def test_expand_file_patterns_deduplication(self, mock_glob):
        """Test file pattern deduplication"""
        mock_glob.side_effect = [['file1.py'], ['file1.py', 'file2.py']]
        
        result = _expand_file_patterns(['pattern1', 'pattern2'])
        
        # Should deduplicate file1.py
        assert result == ['file1.py', 'file2.py']
    
    def test_validate_files_all_valid(self):
        """Test file validation with all valid files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = os.path.join(temp_dir, "file1.py")
            file2 = os.path.join(temp_dir, "file2.py")
            
            # Create test files
            for f in [file1, file2]:
                with open(f, 'w') as fd:
                    fd.write("# test")
            
            result = _validate_files([file1, file2])
            assert len(result) == 2
            assert file1 in result
            assert file2 in result
    
    def test_validate_files_some_invalid(self):
        """Test file validation with some invalid files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_file = os.path.join(temp_dir, "valid.py")
            invalid_file = os.path.join(temp_dir, "nonexistent.py")
            
            # Create only one file
            with open(valid_file, 'w') as f:
                f.write("# test")
            
            result = _validate_files([valid_file, invalid_file])
            assert len(result) == 1
            assert result[0] == valid_file
    
    def test_validate_files_none_valid(self):
        """Test file validation with no valid files"""
        result = _validate_files(["nonexistent1.py", "nonexistent2.py"])
        assert result is None
    
    @patch('cli_file.asyncio.run')
    @patch('cli_file.process_multiple_files_async')
    def test_process_multiple_files(self, mock_process_async, mock_asyncio_run):
        """Test multiple files processing"""
        mock_args = Mock()
        mock_args.host = 'http://localhost:11434'
        mock_args.model = 'test-model'
        mock_args.output = False
        mock_args.concurrent = 4
        mock_args.output_dir = None
        mock_args.stream = False
        
        files = ['file1.py', 'file2.py']
        
        result = _process_multiple_files(mock_args, files)
        
        assert result == 0
        mock_asyncio_run.assert_called_once()
    
    @patch('cli_file.read_file_content')
    @patch('cli_file.get_static_analysis_issues')
    @patch('cli_file.analyze_file_with_ollama_sync')
    def test_process_single_file_with_issues(self, mock_analyze, mock_get_issues, mock_read_content):
        """Test single file processing with issues found"""
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.stream = False
        mock_args.output = False
        mock_args.host = 'http://localhost:11434'
        mock_args.model = 'test-model'
        mock_args.output_dir = None
        
        mock_read_content.return_value = "print('test')"
        mock_get_issues.return_value = [{'line': 1, 'message': 'test issue'}]
        mock_analyze.return_value = "Analysis result"
        
        result = _process_single_file(mock_args, 'test.py')
        
        assert result == 0
        mock_read_content.assert_called_once_with('test.py')
        mock_get_issues.assert_called_once_with('test.py')
        mock_analyze.assert_called_once()
    
    @patch('cli_file.read_file_content')
    @patch('cli_file.get_static_analysis_issues')
    @pytest.mark.filterwarnings("ignore:coroutine.*was never awaited:RuntimeWarning")
    def test_process_single_file_no_issues(self, mock_get_issues, mock_read_content):
        """Test single file processing with no issues"""
        mock_args = Mock()
        mock_read_content.return_value = "# clean code"
        mock_get_issues.return_value = []  # No issues
        
        result = _process_single_file(mock_args, 'test.py')
        
        assert result == 0
        mock_read_content.assert_called_once_with('test.py')
        mock_get_issues.assert_called_once_with('test.py')
    
    @patch('cli_file.read_file_content')
    def test_process_single_file_read_error(self, mock_read_content):
        """Test single file processing with read error"""
        mock_args = Mock()
        mock_read_content.return_value = None  # Read error
        
        result = _process_single_file(mock_args, 'test.py')
        
        assert result == 1


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_file_filtering_integration(self):
        """Test complete file filtering workflow"""
        # Create some test files
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_file = os.path.join(temp_dir, "valid.py")
            with open(valid_file, 'w') as f:
                f.write("# Valid file")
            
            all_files = [valid_file, "nonexistent.py"]
            valid_files = [f for f in all_files if os.path.exists(f) and os.path.isfile(f)]
            
            assert len(valid_files) == 1
            assert valid_files[0] == valid_file
    
    @patch('cli_file.analyze_file_with_ollama_sync')
    @patch('cli_file.get_static_analysis_issues')
    def test_single_file_workflow_with_issues(self, mock_get_issues, mock_analyze):
        """Test complete workflow for single file with issues"""
        # Setup mocks
        mock_get_issues.return_value = [
            {'line': 1, 'type': 'code_smell', 'severity': 'MINOR', 'message': 'Test issue'}
        ]
        mock_analyze.return_value = "Analysis result"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('test')")
            temp_file = f.name
        
        try:
            # Create parser and parse args
            parser = _create_argument_parser()
            args = parser.parse_args([temp_file])
            
            # Process single file
            result = _process_single_file(args, temp_file)
            
            assert result == 0
            mock_get_issues.assert_called_once_with(temp_file)
            mock_analyze.assert_called_once()
        finally:
            os.unlink(temp_file)
    
    @patch('cli_file.analyze_file_with_ollama_sync')
    @patch('cli_file.get_static_analysis_issues')
    def test_single_file_workflow_no_issues(self, mock_get_issues, mock_analyze):
        """Test complete workflow for single file without issues"""
        # Setup mocks
        mock_get_issues.return_value = []  # No issues
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# Clean code")
            temp_file = f.name
        
        try:
            # Create parser and parse args
            parser = _create_argument_parser()
            args = parser.parse_args([temp_file])
            
            # Process single file
            result = _process_single_file(args, temp_file)
            
            assert result == 0
            mock_get_issues.assert_called_once_with(temp_file)
            # Analyze should NOT be called when no issues
            mock_analyze.assert_not_called()
        finally:
            os.unlink(temp_file)
    
    @patch('cli_file.asyncio.run')
    @patch('cli_file.process_multiple_files_async')
    def test_multiple_files_workflow(self, mock_process_async, mock_asyncio_run):
        """Test complete workflow for multiple files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = os.path.join(temp_dir, "file1.py")
            file2 = os.path.join(temp_dir, "file2.py")
            
            for f in [file1, file2]:
                with open(f, 'w') as fd:
                    fd.write("# Test file")
            
            # Create parser and parse args
            parser = _create_argument_parser()
            args = parser.parse_args([file1, file2, '--concurrent', '2'])
            
            # Process multiple files
            result = _process_multiple_files(args, [file1, file2])
            
            assert result == 0
            mock_asyncio_run.assert_called_once()
            assert mock_process_async.called
    
    @pytest.mark.filterwarnings("ignore:coroutine.*was never awaited:RuntimeWarning")
    def test_output_to_markdown_workflow(self):
        """Test complete workflow with markdown output"""
        with patch('cli_file.save_to_markdown') as mock_save, \
             patch('cli_file.analyze_file_with_ollama_sync') as mock_analyze, \
             patch('cli_file.get_static_analysis_issues') as mock_get_issues:
            
            # Setup mocks explicitly as regular Mock objects
            mock_get_issues.return_value = [
                {'line': 1, 'type': 'code_smell', 'severity': 'MINOR', 'message': 'Test issue'}
            ]
            mock_analyze.return_value = "# Analysis Report\n\nTest analysis"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write("print('test')")
                temp_file = f.name
            
            try:
                # Create parser with output flag
                parser = _create_argument_parser()
                args = parser.parse_args([temp_file, '--output'])
                
                # Process file
                result = _process_single_file(args, temp_file)
                
                assert result == 0
                mock_save.assert_called_once()
                # Verify save was called with correct arguments
                save_args = mock_save.call_args[0]
                assert save_args[1] == "# Analysis Report\n\nTest analysis"  # content
                assert save_args[2] == temp_file  # analyzed_file
            finally:
                os.unlink(temp_file)
    
    @patch('glob.glob')
    def test_glob_pattern_workflow(self, mock_glob):
        """Test complete workflow with glob patterns"""
        # Mock glob to return specific files
        mock_glob.return_value = ['src/file1.py', 'src/file2.py']
        
        # Test expansion
        expanded = _expand_file_patterns(['src/*.py'])
        
        assert len(expanded) == 2
        assert 'src/file1.py' in expanded
        assert 'src/file2.py' in expanded
        mock_glob.assert_called_once_with('src/*.py')
    
    def test_end_to_end_static_analysis(self):
        """Test end-to-end static analysis detection"""
        # Create a file with known issues
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""import unused_module
# TODO: Fix this later
print("Debug message")
password="hardcoded123"
try:
    risky_operation()
except:
    pass
""")
            temp_file = f.name
        
        try:
            # Run static analysis
            issues = get_static_analysis_issues(temp_file)
            
            # Verify all issue types are detected
            issue_types = {issue['type'] for issue in issues}
            assert 'code_smell' in issue_types  # TODO and print
            assert 'vulnerability' in issue_types  # hardcoded password
            assert 'bug' in issue_types  # empty except
            
            # Verify specific issues
            todo_issues = [i for i in issues if 'TODO' in i['message']]
            assert len(todo_issues) > 0
            
            print_issues = [i for i in issues if 'logger' in i['message']]
            assert len(print_issues) > 0
            
            password_issues = [i for i in issues if 'credential' in i['message']]
            assert len(password_issues) > 0
        finally:
            os.unlink(temp_file)