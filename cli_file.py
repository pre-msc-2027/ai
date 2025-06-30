#!/usr/bin/env python3
"""
Ollama AI CLI Tool - File Analysis using Ollama
Analyzes code files and provides recommendations using static analysis
"""

import argparse
import os
from pathlib import Path
from ollama import Client
from datetime import datetime


def get_static_analysis_issues(file_path):
    """Perform static analysis to find code issues"""
    try:
        print("🔍 Running static analysis...")
        issues = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # TODO/FIXME comments
            if 'TODO' in line.upper() or 'FIXME' in line.upper():
                issues.append({
                    'line': i,
                    'type': 'code_smell',
                    'severity': 'INFO',
                    'message': 'Complete the task associated to this TODO comment',
                    'code': line.strip()
                })
            
            # Print statements in Python (should use logging)
            if 'print(' in line and file_path.endswith('.py'):
                issues.append({
                    'line': i,
                    'type': 'code_smell',
                    'severity': 'MINOR',
                    'message': 'Replace this use of System.out or System.err by a logger',
                    'code': line.strip()
                })
            
            # Long lines
            if len(line) > 120:
                issues.append({
                    'line': i,
                    'type': 'code_smell',
                    'severity': 'MINOR',
                    'message': 'Split this 120 characters long line (which is greater than 120 authorized)',
                    'code': line.strip()[:50] + '...'
                })
            
            # Empty catch blocks (Python)
            if file_path.endswith('.py') and 'except:' in stripped_line and i < len(lines):
                next_line = lines[i].strip() if i < len(lines) else ""
                if next_line == "pass":
                    issues.append({
                        'line': i,
                        'type': 'bug',
                        'severity': 'MAJOR',
                        'message': 'Handle the exception or explain in a comment why it can be ignored',
                        'code': f"{stripped_line}\\n{next_line}"
                    })
            
            # Hardcoded credentials
            if any(keyword in line.lower() for keyword in ['password=', 'secret=', 'api_key=', 'token=']):
                if not line.strip().startswith('#'):  # Not a comment
                    issues.append({
                        'line': i,
                        'type': 'vulnerability',
                        'severity': 'BLOCKER',
                        'message': 'Review this hardcoded credential',
                        'code': line.strip()
                    })
            
            # Unused imports (Python)
            if file_path.endswith('.py') and line.strip().startswith('import ') and 'import os' not in line:
                # Simple check - could be improved with AST analysis
                import_name = line.split('import ')[1].split(' as ')[0].split('.')[0].strip()
                if import_name not in content[content.find(line) + len(line):]:
                    issues.append({
                        'line': i,
                        'type': 'code_smell',
                        'severity': 'MINOR',
                        'message': f'Unused import: {import_name}',
                        'code': line.strip()
                    })
        
        if issues:
            print(f"✅ Found {len(issues)} static analysis issues")
        else:
            print("✅ No issues found")
            
        return issues
        
    except Exception as e:
        print(f"⚠️  Error during static analysis: {e}")
        return []


def read_file_content(file_path):
    """Read and return file content with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except PermissionError:
        print(f"Error: Permission denied to read '{file_path}'.")
        return None
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return None


def generate_output_filename(input_file):
    """Generate output filename with timestamp"""
    base_name = Path(input_file).stem
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    return f"{base_name}_analysis_{timestamp}.md"


def save_to_markdown(output_file, content, analyzed_file):
    """Save analysis content to a markdown file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Analysis Report for {analyzed_file}\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(content)
        print(f"\n✅ Analysis saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving to file: {e}")


def analyze_file_with_ollama(file_path, content, is_streaming, sonar_issues=None, save_to_file=False):
    """Send file content to Ollama for analysis"""
    # Configure Ollama client with external URL
    client = Client(host='http://10.0.0.1:11434')
    model = 'gemma3:12b'
    
    # Get file extension for context
    file_ext = Path(file_path).suffix.lower()
    
    # Determine file type for better analysis
    language_map = {
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
    
    language = language_map.get(file_ext, 'Unknown')
    
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
    prompt = f"""
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
    
    try:
        if not save_to_file:
            print(f"🔍 Analyzing {language} file: {file_path}")
            print(f"📊 File size: {len(content)} characters")
            print("🤖 Sending to Ollama for analysis...\n")
        else:
            print(f"🔍 Analyzing {language} file: {file_path}")
            print("🤖 Generating analysis report...")
        
        # Send prompt to Ollama
        response = client.chat(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a SonarQube issue resolver. Follow the exact format provided. Address ONLY the specific SonarQube issues listed. Do not provide general analysis or additional suggestions. Be precise, technical, and stick to the required structure. IMPORTANT: Format your entire response in proper Markdown syntax with appropriate headers, code blocks, lists, and emphasis.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            stream=is_streaming,
        )

        if is_streaming:
            full_response = ""
            for chunk in response:
                content_chunk = chunk['message']['content']
                if not save_to_file:
                    print(content_chunk, end='', flush=True)
                full_response += content_chunk
            return full_response
        else:
            # Extract and display response
            if 'message' in response and 'content' in response['message']:
                response_content = response['message']['content']
                if not save_to_file:
                    print("=" * 80)
                    print(f"📋 ANALYSIS REPORT FOR: {file_path}")
                    print("=" * 80)
                    print(response_content)
                    print("\n" + "=" * 80)
                    print("✅ Analysis completed!")
                return response_content
            else:
                print("❌ Error: No response content received from Ollama")
                return None
            
    except Exception as e:
        print(f"❌ Error communicating with Ollama: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Ollama AI CLI Tool - File Analysis using Ollama',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
              python cli_file.py mycode.py              # Analyze a Python file
              python cli_file.py src/utils.js           # Analyze a JavaScript file
              python cli_file.py config/settings.json   # Analyze a JSON file
        """
    )

    parser.add_argument('file', help='Path to the file to analyze')
    parser.add_argument('-s', '--stream', action='store_true', help='Language to use')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose output')
    parser.add_argument('-o', '--output', action='store_true',
                       help='Save the analysis to a markdown file')

    args = parser.parse_args()

    # Check if file exists
    if not os.path.exists(args.file):
        print(f"❌ Error: File '{args.file}' does not exist.")
        return 1

    # Check if it's a file (not a directory)
    if not os.path.isfile(args.file):
        print(f"❌ Error: '{args.file}' is not a file.")
        return 1

    # Read file content
    content = read_file_content(args.file)
    if content is None:
        return 1

    # Check file size (limit to avoid overwhelming the model)
    max_size = 100000  # 100KB limit
    if len(content) > max_size:
        print(f"⚠️  Warning: File is large ({len(content)} chars). Truncating to {max_size} characters.")
        content = content[:max_size] + "\n... (truncated)"

    # Get static analysis issues for the file
    print("🔍 Checking for code issues...")
    sonar_issues = get_static_analysis_issues(args.file)
    
    if sonar_issues:
        print(f"⚠️  Found {len(sonar_issues)} code issues")
        if args.verbose:
            for issue in sonar_issues:
                print(f"  - Line {issue.get('line', 'N/A')}: {issue.get('message', 'No message')}")
        
        if args.verbose:
            print(f"📁 File: {args.file}")
            print(f"📏 Size: {len(content)} characters")
            print(f"🔤 First 200 chars: {content[:200]}...")
            print()

        # Override streaming if output file is specified
        is_streaming = args.stream and not args.output
        
        # Analyze with Ollama only if code issues are found
        response = analyze_file_with_ollama(args.file, content, is_streaming, sonar_issues, args.output)
        
        # Save to markdown if output flag is specified
        if args.output and response:
            output_filename = generate_output_filename(args.file)
            save_to_markdown(output_filename, response, args.file)
    else:
        print("✅ No code issues detected - Analysis skipped")
    
    return 0


if __name__ == "__main__":
    exit(main())