#!/usr/bin/env python3
"""
Ollama AI CLI Tool - Simple POC using Ollama
"""

import argparse
from ollama import Client


def send_prompt(prompt, is_streaming):
    # Configure Ollama client with external URL
    client = Client(host='http://10.0.0.1:11434')
    model = 'gemma3:12b'

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

def main():
    parser = argparse.ArgumentParser(
        description='Ollama AI CLI Tool - Simple POC using Ollama'
    )

    parser.add_argument('prompt', help='Prompt to send to AI')
    parser.add_argument('-s', '--stream', action='store_true', help='Stream output')

    args = parser.parse_args()

    send_prompt(args.prompt, args.stream)

if __name__ == "__main__":
    main()