#!/usr/bin/env python3
"""
Ollama AI CLI Tool - Simple POC using Ollama
"""

import argparse
import asyncio
from ollama import Client, AsyncClient


def send_prompt_sync(host, model, prompt, is_streaming):
    """Send prompt synchronously using the standard Client"""
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


async def send_prompt_async(host, model, prompt, is_streaming):
    """Send prompt asynchronously using AsyncClient"""
    # Configure Ollama client with external URL
    client = AsyncClient(host=host)

    # Send prompt to Ollama
    response = await client.chat(
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
        async for chunk in response:
            print(chunk['message']['content'], end='', flush=True)
    else:
        # Extract and display response
        if 'message' in response and 'content' in response['message']:
            print(response['message']['content'])


def main():
    parser = argparse.ArgumentParser(
        description='Ollama AI CLI Tool - Simple POC using Ollama',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
              python cli.py "What is Python?"                  # Synchronous mode
              python cli.py "What is Python?" --async          # Asynchronous mode
              python cli.py "Explain Docker" -s                # Stream output
              python cli.py "Hello" -m llama3:8b              # Use different model
        """
    )

    parser.add_argument('--host', default='http://10.0.0.1:11434',
                        help='Ollama server URL (default: http://10.0.0.1:11434)')
    parser.add_argument('-m', '--model', default='mistral:latest',
                        help='Ollama model to use (default: mistral:latest)')
    parser.add_argument('prompt', help='Prompt to send to AI')
    parser.add_argument('-s', '--stream', action='store_true', help='Stream output')
    parser.add_argument('--async', dest='use_async', action='store_true', 
                        help='Use asynchronous mode')

    args = parser.parse_args()

    if args.use_async:
        # Run asynchronously
        asyncio.run(send_prompt_async(args.host, args.model, args.prompt, args.stream))
    else:
        # Run synchronously
        send_prompt_sync(args.host, args.model, args.prompt, args.stream)


if __name__ == "__main__":
    main()