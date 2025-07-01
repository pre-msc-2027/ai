#!/usr/bin/env python3
"""
Ollama AI CLI Tool - File Analysis using Ollama
Analyzes code files and provides recommendations using static analysis
"""

import argparse
import os
import asyncio
import logging
import time
from pathlib import Path
from ollama import Client, AsyncClient
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Language mapping for file extensions
LANGUAGE_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.java': 'Java',
    '.cpp': 'C++',
    '.c': 'C',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.sh': 'Shell/Bash',
    '.sql': 'SQL',
    '.html': 'HTML',
    '.css': 'CSS',
    '.json': 'JSON',
    '.xml': 'XML',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.md': 'Markdown'
}


def build_sonar_analysis_prompt(language, file_path, sonar_issues, content):
    """Build the analysis prompt for SonarQube issues"""
    # Build SonarQube issues section if available
    sonar_section = ""
    if sonar_issues and len(sonar_issues) > 0:
        sonar_section = f"""

**SonarQube Issues Detected ({len(sonar_issues)} issues):**
"""
        for i, issue in enumerate(sonar_issues, 1):
            sonar_section += f"""
{i}. **{issue.get('type', 'Issue').upper()}** (Line {issue.get('line', 'N/A')}) - {issue.get('severity', 'UNKNOWN')}
   Message: {issue.get('message', 'No message')}
   Code: `{issue.get('code', 'N/A')}`
"""
        sonar_section += "\nPlease address these SonarQube issues in your analysis and provide specific recommendations for fixing each one.\n"

    # Build analysis prompt focused only on SonarQube issues
    return f"""
        You are a SonarQube issue resolver. Analyze ONLY the SonarQube issues detected in the {language} file: {file_path}

        {sonar_section}
        
        For each SonarQube issue listed above, provide a response in this EXACT format:
        
        ## Issue #[NUMBER]
        **Location:** Line [LINE_NUMBER]
        **Type:** [ISSUE_TYPE]
        **Severity:** [SEVERITY_LEVEL]
        **Problem:** [BRIEF_DESCRIPTION]
        
        **Root Cause:**
        [Explain why this is an issue in 1-2 sentences]
        
        **Solution:**
        [Provide the exact code fix]
        
        **Original Code:**
        ```{language.lower()}
        [Show the problematic code]
        ```
        
        **Fixed Code:**
        ```{language.lower()}
        [Show the corrected code]
        ```
        
        **Why This Fix Works:**
        [Explain in 1-2 sentences why this solution resolves the issue]
        
        ---
        
        IMPORTANT: 
        - Address ONLY the SonarQube issues provided
        - Do NOT add general code analysis or suggestions
        - Use the exact format above for each issue
        - Provide working code solutions
        - Keep explanations concise and technical
        
        **File Content for Reference:**
        ```{language.lower()}
        {content}
        ```
    """


def check_todo_comments(line, line_number):
    """Check for TODO/FIXME comments"""
    if 'TODO' in line.upper() or 'FIXME' in line.upper():
        return {
            'line': line_number,
            'type': 'code_smell',
            'severity': 'INFO',
            'message': 'Complete the task associated to this TODO comment',
            'code': line.strip()
        }
    return None


def check_print_statements(line, line_number, file_path):
    """Check for print statements in Python files"""
    if 'print(' in line and file_path.endswith('.py'):
        return {
            'line': line_number,
            'type': 'code_smell',
            'severity': 'MINOR',
            'message': 'Replace this use of System.out or System.err by a logger',
            'code': line.strip()
        }
    return None


def check_long_lines(line, line_number):
    """Check for lines that are too long"""
    if len(line) > 120:
        return {
            'line': line_number,
            'type': 'code_smell',
            'severity': 'MINOR',
            'message': 'Split this 120 characters long line (which is greater than 120 authorized)',
            'code': line.strip()[:50] + '...'
        }
    return None


def check_empty_catch_blocks(line, line_number, lines, file_path):
    """Check for empty catch blocks in Python"""
    stripped_line = line.strip()
    if file_path.endswith('.py') and 'except:' in stripped_line and line_number < len(lines):
        next_line = lines[line_number].strip() if line_number < len(lines) else ""
        if next_line.startswith("pass"):
            return {
                'line': line_number,
                'type': 'bug',
                'severity': 'MAJOR',
                'message': 'Handle the exception or explain in a comment why it can be ignored',
                'code': f"{stripped_line}\\n{next_line}"
            }
    return None


def check_hardcoded_credentials(line, line_number):
    """Check for hardcoded credentials"""
    keywords = ['password=', 'secret=', 'api_key=', 'token=', 'secret_key']
    if any(keyword in line.lower() for keyword in keywords):
        if not line.strip().startswith('#'):  # Not a comment
            return {
                'line': line_number,
                'type': 'vulnerability',
                'severity': 'BLOCKER',
                'message': 'Review this hardcoded credential',
                'code': line.strip()
            }
    return None


def check_unused_imports(line, line_number, content, file_path):
    """Check for unused imports in Python files"""
    if file_path.endswith('.py') and line.strip().startswith('import ') and 'import os' not in line:
        try:
            import_name = line.split('import ')[1].split(' as ')[0].split('.')[0].strip()
            if import_name not in content[content.find(line) + len(line):]:
                return {
                    'line': line_number,
                    'type': 'code_smell',
                    'severity': 'MINOR',
                    'message': f'Unused import: {import_name}',
                    'code': line.strip()
                }
        except IndexError:
            pass  # Skip malformed import lines
    return None


def get_static_analysis_issues(file_path):
    """Perform static analysis to find code issues"""
    try:
        logger.info("🔍 Running static analysis...")
        issues = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # List of checker functions
        checkers = [
            lambda line, i: check_todo_comments(line, i),
            lambda line, i: check_print_statements(line, i, file_path),
            lambda line, i: check_long_lines(line, i),
            lambda line, i: check_empty_catch_blocks(line, i, lines, file_path),
            lambda line, i: check_hardcoded_credentials(line, i),
            lambda line, i: check_unused_imports(line, i, content, file_path),
        ]
        
        for i, line in enumerate(lines, 1):
            for checker in checkers:
                issue = checker(line, i)
                if issue:
                    issues.append(issue)
        
        if issues:
            logger.info(f"✅ Found {len(issues)} static analysis issues")
        else:
            logger.info("✅ No issues found")
            
        return issues
        
    except Exception as e:
        logger.error(f"⚠️  Error during static analysis: {e}")
        return []


def read_file_content(file_path):
    """Read and return file content with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        logger.error(f"Error: File '{file_path}' not found.")
        return None
    except PermissionError:
        logger.error(f"Error: Permission denied to read '{file_path}'.")
        return None
    except Exception as e:
        logger.error(f"Error reading file '{file_path}': {e}")
        return None


def generate_output_filename(input_file):
    """Generate output filename with timestamp"""
    base_name = Path(input_file).stem
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    return f"{base_name}_analysis_{timestamp}.md"


def save_to_markdown(output_file, content, analyzed_file, output_dir=None):
    """Save analysis content to a markdown file"""
    try:
        # Determine full output path
        if output_dir:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_file)
        else:
            output_path = output_file
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Analysis Report for {analyzed_file}\\n\\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            f.write(content)
        logger.info(f"✅ Analysis saved to: {output_path}")
    except Exception as e:
        logger.error(f"❌ Error saving to file: {e}")


def _prepare_analysis_context(file_path, content, sonar_issues):
    """Prepare analysis context and prompt"""
    file_ext = Path(file_path).suffix.lower()
    language = LANGUAGE_MAP.get(file_ext, 'Unknown')
    prompt = build_sonar_analysis_prompt(language, file_path, sonar_issues, content)
    return language, prompt


def _log_analysis_start(language, file_path, content, save_to_file):
    """Log analysis start information"""
    if not save_to_file:
        logger.info(f"🔍 Analyzing {language} file: {file_path}")
        logger.debug(f"📊 File size: {len(content)} characters")
        logger.info("🤖 Sending to Ollama for analysis...")
    else:
        logger.info(f"🔍 Analyzing {language} file: {file_path}")
        logger.info("🤖 Generating analysis report...")


def _get_system_message():
    """Get the system message for Ollama"""
    return {
        'role': 'system',
        'content': 'You are a SonarQube issue resolver. Follow the exact format provided. Address ONLY the specific SonarQube issues listed. Do not provide general analysis or additional suggestions. Be precise, technical, and stick to the required structure. IMPORTANT: Format your entire response in proper Markdown syntax with appropriate headers, code blocks, lists, and emphasis.'
    }


def _process_streaming_response(response, save_to_file):
    """Process streaming response from Ollama"""
    full_response = ""
    for chunk in response:
        content_chunk = chunk['message']['content']
        if not save_to_file:
            print(content_chunk, end='', flush=True)
        full_response += content_chunk
    return full_response


async def _process_async_streaming_response(response, save_to_file):
    """Process async streaming response from Ollama"""
    full_response = ""
    async for chunk in response:
        content_chunk = chunk['message']['content']
        if not save_to_file:
            print(content_chunk, end='', flush=True)
        full_response += content_chunk
    return full_response


def _process_non_streaming_response(response, file_path, save_to_file):
    """Process non-streaming response from Ollama"""
    if 'message' in response and 'content' in response['message']:
        response_content = response['message']['content']
        if not save_to_file:
            print("=" * 80)
            print(f"📋 ANALYSIS REPORT FOR: {file_path}")
            print("=" * 80)
            print(response_content)
            print("\\n" + "=" * 80)
            logger.info("✅ Analysis completed!")
        return response_content
    else:
        logger.error("❌ Error: No response content received from Ollama")
        return None


def analyze_file_with_ollama_sync(host, model, file_path, content, is_streaming, sonar_issues=None, save_to_file=False):
    """Send file content to Ollama for analysis synchronously"""
    try:
        # Prepare analysis context
        language, prompt = _prepare_analysis_context(file_path, content, sonar_issues)
        _log_analysis_start(language, file_path, content, save_to_file)
        
        # Configure Ollama client
        client = Client(host=host)
        
        # Send prompt to Ollama
        response = client.chat(
            model=model,
            messages=[
                _get_system_message(),
                {'role': 'user', 'content': prompt}
            ],
            stream=is_streaming,
        )

        # Process response
        if is_streaming:
            return _process_streaming_response(response, save_to_file)
        else:
            return _process_non_streaming_response(response, file_path, save_to_file)
            
    except Exception as e:
        logger.error(f"❌ Error communicating with Ollama: {e}")
        return None


async def analyze_file_with_ollama_async(host, model, file_path, content, is_streaming, sonar_issues=None, save_to_file=False):
    """Send file content to Ollama for analysis asynchronously"""
    try:
        # Prepare analysis context
        language, prompt = _prepare_analysis_context(file_path, content, sonar_issues)
        _log_analysis_start(language, file_path, content, save_to_file)
        
        # Configure Ollama client
        client = AsyncClient(host=host)
        
        # Send prompt to Ollama asynchronously
        response = await client.chat(
            model=model,
            messages=[
                _get_system_message(),
                {'role': 'user', 'content': prompt}
            ],
            stream=is_streaming,
        )

        # Process response
        if is_streaming:
            return await _process_async_streaming_response(response, save_to_file)
        else:
            return _process_non_streaming_response(response, file_path, save_to_file)
            
    except Exception as e:
        logger.error(f"❌ Error communicating with Ollama: {e}")
        return None


async def process_multiple_files_async(host, model, file_paths, save_output=False, max_concurrent=3, output_dir=None, stream_enabled=False):
    """Process multiple files concurrently with rate limiting"""
    start_total = time.time()
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_file(file_path):
        async with semaphore:
            start_time = time.time()
            logger.info(f"⏳ Processing: {file_path}")
            
            # Read file content
            content = read_file_content(file_path)
            if content is None:
                return None
            
            # Check file size
            max_size = 100000  # 100KB limit
            if len(content) > max_size:
                logger.warning(f"⚠️  Warning: File is large ({len(content)} chars). Truncating to {max_size} characters.")
                content = content[:max_size] + "\\n... (truncated)"
            
            # Get static analysis issues
            sonar_issues = get_static_analysis_issues(file_path)
            
            if sonar_issues:
                logger.info(f"⚠️  Found {len(sonar_issues)} code issues")
                
                # Analyze with Ollama - consistent streaming logic with sync mode
                is_streaming = stream_enabled and not save_output
                response = await analyze_file_with_ollama_async(host, model, file_path, content, is_streaming, sonar_issues, save_output)
                
                # Save to markdown if requested
                if save_output and response:
                    output_filename = generate_output_filename(file_path)
                    save_to_markdown(output_filename, response, file_path, output_dir)
                
                elapsed_time = time.time() - start_time
                logger.info(f"✅ Completed {file_path} in {elapsed_time:.1f}s")
                return response
            else:
                elapsed_time = time.time() - start_time
                logger.info(f"✅ No code issues detected - Analysis skipped ({elapsed_time:.1f}s)")
                return None
    
    # Process all files concurrently
    tasks = [process_file(fp) for fp in file_paths]
    results = await asyncio.gather(*tasks)
    
    # Performance summary
    total_time = time.time() - start_total
    successful_files = sum(1 for r in results if r is not None)
    logger.info(f"🏁 Async processing completed: {successful_files}/{len(file_paths)} files in {total_time:.1f}s")
    
    return results




def main():
    parser = argparse.ArgumentParser(
        description='Ollama AI CLI Tool - File Analysis using Ollama',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
              python cli_file.py mycode.py              # Analyze a Python file
              python cli_file.py src/utils.js           # Analyze a JavaScript file
              python cli_file.py config/settings.json   # Analyze a JSON file
              python cli_file.py mycode.py -o           # Save analysis to markdown
              python cli_file.py src/*.py --concurrent 5        # Multiple files (auto-async) with 5 concurrent requests
        """
    )

    parser.add_argument('--host', default='http://10.0.0.1:11434',
                        help='Ollama server URL (default: http://10.0.0.1:11434)')
    parser.add_argument('-m', '--model', default='mistral:latest',
                        help='Ollama model to use (default: mistral:latest)')
    parser.add_argument('file', nargs='+', help='Path to the file(s) to analyze')
    parser.add_argument('--stream', action='store_true', help='Stream output')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose output')
    parser.add_argument('-o', '--output', action='store_true',
                       help='Save the analysis to a markdown file')
    parser.add_argument('--output-dir', type=str,
                        help='Directory to save markdown files (created if not exists)')
    parser.add_argument('--concurrent', type=int, default=4,
                       help='Maximum number of concurrent requests in async mode (default: 4)')

    args = parser.parse_args()

    # Configure logging level based on verbose flag
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Expand glob patterns if any
    import glob
    all_files = []
    for pattern in args.file:
        matched_files = glob.glob(pattern)
        if matched_files:
            all_files.extend(matched_files)
        else:
            # If no glob match, treat as literal file path
            all_files.append(pattern)
    
    # Remove duplicates while preserving order
    all_files = list(dict.fromkeys(all_files))
    
    # Filter out non-existent files
    valid_files = []
    for file_path in all_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            valid_files.append(file_path)
        else:
            logger.error(f"❌ Error: '{file_path}' does not exist or is not a file.")
    
    if not valid_files:
        logger.error("❌ No valid files to analyze.")
        return 1

    # Auto-enable async mode for multiple files
    use_async = len(valid_files) > 1
    
    if use_async:
        logger.info(f"🚀 Analyzing {len(valid_files)} file(s) in async mode with max {args.concurrent} concurrent requests...")
        asyncio.run(process_multiple_files_async(args.host, args.model, valid_files, args.output, args.concurrent, args.output_dir, args.stream))
        return 0
    else:
        # Single file sync mode
        file_path = valid_files[0]
        content = read_file_content(file_path)
        if content is None:
            return 1

        # Check file size
        max_size = 100000  # 100KB limit
        if len(content) > max_size:
            logger.warning(f"⚠️  Warning: File is large ({len(content)} chars). Truncating to {max_size} characters.")
            content = content[:max_size] + "\\n... (truncated)"

        # Get static analysis issues for the file
        logger.info("🔍 Checking for code issues...")
        sonar_issues = get_static_analysis_issues(file_path)
        
        if sonar_issues:
            logger.info(f"⚠️  Found {len(sonar_issues)} code issues")
            if args.verbose:
                for issue in sonar_issues:
                    logger.debug(f"  - Line {issue.get('line', 'N/A')}: {issue.get('message', 'No message')}")
            
            if args.verbose:
                logger.debug(f"📁 File: {file_path}")
                logger.debug(f"📏 Size: {len(content)} characters")
                logger.debug(f"🔤 First 200 chars: {content[:200]}...")

            # Override streaming if output file is specified
            is_streaming = args.stream and not args.output
            
            # Analyze with Ollama only if code issues are found
            response = analyze_file_with_ollama_sync(args.host, args.model, file_path, content, is_streaming, sonar_issues, args.output)
            
            # Save to markdown if output flag is specified
            if args.output and response:
                output_filename = generate_output_filename(file_path)
                save_to_markdown(output_filename, response, file_path, args.output_dir)
        else:
            logger.info("✅ No code issues detected - Analysis skipped")
    
    return 0


if __name__ == "__main__":
    exit(main())