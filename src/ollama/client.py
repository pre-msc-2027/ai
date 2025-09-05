import logging

import ollama


def send_prompt_to_ollama(prompt: str, model: str, host: str) -> str:
    logging.debug("Initializing Ollama client")
    logging.debug(f"   Host: {host}")
    logging.debug(f"   Model: {model}")
    logging.debug(f"   Prompt length: {len(prompt)} characters")

    client = ollama.Client(host=host)

    try:
        logging.debug("Sending chat request to Ollama...")
        logging.debug("Forcing JSON format output")

        # Log the first and last parts of the prompt for debugging
        prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
        logging.debug(f"Prompt preview: {prompt_preview}")

        response = client.chat(
            model=model, messages=[{"role": "user", "content": prompt}], format="json"
        )

        logging.debug("Raw Ollama response received")
        logging.debug(f"   Full response structure: {response}")

        content = response["message"]["content"]
        logging.debug(f"Extracted content length: {len(content)} characters")
        logging.debug(
            f"Content preview: {content[:200]}{'...' if len(content) > 200 else ''}"
        )

        logging.debug("Ollama request successful")
        return content

    except Exception as e:
        logging.error(f"Erreur lors de l'appel à Ollama : {e}")
        logging.debug(f"Ollama exception details: {type(e).__name__}: {e}")

        # Log more details about the error
        if hasattr(e, "response"):
            logging.debug(f"Error response: {e.response}")
        if hasattr(e, "request"):
            logging.debug(f"Error request: {e.request}")

        return "Erreur lors de la génération de la réponse IA."
