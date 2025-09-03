import logging

import ollama


def send_prompt_to_ollama(prompt: str, model: str, host: str) -> str:
    client = ollama.Client(host=host)
    try:
        response = client.chat(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        logging.error(f"Erreur lors de l'appel à Ollama : {e}")
        return "Erreur lors de la génération de la réponse IA."
