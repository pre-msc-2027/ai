#!/usr/bin/env python3
"""
Ollama AI CLI Tool - Simple POC using Ollama
"""

import argparse
import logging
import sys
from typing import Dict, List

import ollama
from ollama import Client

# Configure logging
logger = logging.getLogger(__name__)


def send_prompt(host: str, model: str, prompt: str, is_streaming: bool) -> int:
    """Send prompt to Ollama using the standard Client

    Returns:
        0 on success, 1 on error
    """
    try:
        # Configure Ollama client with external URL
        client = Client(host=host)

        # Send prompt to Ollama
        messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a code analysis assistant. Provide detailed and "
                    "structured analysis of repositories."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        if is_streaming:
            streaming_response = client.chat(
                model=model, messages=messages, stream=True
            )
            for chunk in streaming_response:
                print(chunk["message"]["content"], end="", flush=True)
        else:
            response = client.chat(model=model, messages=messages, stream=False)
            # Extract and display response
            if "message" in response and "content" in response["message"]:
                print(response["message"]["content"])
            else:
                logger.error("Invalid response format from Ollama")
                return 1

        return 0

    except ollama.ResponseError as e:
        logger.error(f"Ollama API error: {e.error}")
        if e.status_code == 404:
            logger.error(f"Model '{model}' not found. Try: ollama pull {model}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(f"Please check if Ollama is running at {host}")
        return 1


def main() -> int:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Ollama AI CLI Tool - Simple POC using Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
              python cli.py "What is Python?"                  # Basic usage
              python cli.py "Explain Docker" --stream          # Stream output
              python cli.py "Hello" -m llama3:8b              # Use different model
              python cli.py "Debug this code" --verbose        # Enable verbose logging
        """,
    )

    parser.add_argument(
        "--host",
        default="http://10.0.0.1:11434",
        help="Ollama server URL (default: http://10.0.0.1:11434)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="mistral:latest",
        help="Ollama model to use (default: mistral:latest)",
    )
    parser.add_argument("prompt", help="Prompt to send to AI")
    parser.add_argument("--stream", action="store_true", help="Stream output")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    args: argparse.Namespace = parser.parse_args()

    # Configure logging level based on verbose flag
    log_level: int = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Send prompt to Ollama
    return send_prompt(args.host, args.model, args.prompt, args.stream)


if __name__ == "__main__":
    sys.exit(main())
