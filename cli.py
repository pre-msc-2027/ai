#!/usr/bin/env python3
"""
Ollama AI CLI Tool - Simple POC using Ollama
"""

import argparse
import logging
from ollama import Client

# Configure logging
logger = logging.getLogger(__name__)


def send_prompt(host, model, prompt, is_streaming):
    """Send prompt to Ollama using the standard Client"""
    try:
        # Configure Ollama client with external URL
        client = Client(host=host)

        # Send prompt to Ollama
        response = client.chat(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a code analysis assistant. Provide detailed and structured analysis of repositories.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            stream=is_streaming
        )

        if is_streaming:
            for chunk in response:
                print(chunk['message']['content'], end='', flush=True)
        else:
            # Extract and display response
            if 'message' in response and 'content' in response['message']:
                print(response['message']['content'])
    except Exception as e:
        logger.error(f"Error communicating with Ollama: {e}")



def main():
    parser = argparse.ArgumentParser(
        description='Ollama AI CLI Tool - Simple POC using Ollama',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
              python cli.py "What is Python?"                  # Basic usage
              python cli.py "Explain Docker" --stream          # Stream output
              python cli.py "Hello" -m llama3:8b              # Use different model
              python cli.py "Debug this code" --verbose        # Enable verbose logging
        """
    )

    parser.add_argument('--host', default='http://10.0.0.1:11434',
                        help='Ollama server URL (default: http://10.0.0.1:11434)')
    parser.add_argument('-m', '--model', default='mistral:latest',
                        help='Ollama model to use (default: mistral:latest)')
    parser.add_argument('prompt', help='Prompt to send to AI')
    parser.add_argument('--stream', action='store_true', help='Stream output')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    # Configure logging level based on verbose flag
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Send prompt to Ollama
    send_prompt(args.host, args.model, args.prompt, args.stream)


if __name__ == "__main__":
    main()