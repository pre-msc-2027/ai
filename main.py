import argparse
import logging
from typing import Any, List, Optional, Tuple

from ollama import Client
import requests

from src.prompt_builder import build_prompt


def get_issues(
    scan_id: str, api_url: str = "http://localhost:8000/api/scans/analyse_with_rules"
) -> Tuple[List[Any], Optional[str]]:
    try:
        response = requests.get(f"{api_url}/{scan_id}")
        response.raise_for_status()
        data = response.json()
        return data.get("issues", []), data.get("project_path")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de la récupération des issues : {e}")
        return [], None


def main():
    parser = argparse.ArgumentParser(description="Lance l’analyse IA d’un projet")
    parser.add_argument(
        "--host", default="http://10.0.0.1:11434", help="URL du serveur Ollama"
    )
    parser.add_argument(
        "--model",
        default="llama3.1:latest",
        help="Modèle à utiliser (ex: llama3.1:latest)",
    )
    parser.add_argument("--scan-id", required=True, help="Identifiant du scan")
    parser.add_argument(
        "--stream", action="store_true", help="Afficher la réponse en streaming"
    )
    parser.add_argument("--verbose", action="store_true", help="Afficher plus de logs")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    logging.info(f"Lancement de l’analyse IA pour le scan {args.scan_id}")

    issues, project_path = get_issues(args.scan_id)

    def extract_code_snippet(filepath, line_number, context=2):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            start = max(line_number - context - 1, 0)
            end = min(line_number + context, len(lines))
            snippet = "".join(lines[start:end])
            return snippet
        except Exception as e:
            logging.warning(f"Impossible de lire le fichier {filepath} : {e}")
            return "# Code non disponible (erreur de lecture)"

    prompts = []

    for issue in issues:
        code_snippet = extract_code_snippet(issue["file"], issue["line"])
        prompt = build_prompt(
            code_snippet=code_snippet,
            rule=issue["rule_details"],
            file_path=issue["file"],
            line_number=issue["line"],
        )
        prompts.append({"issue_id": issue["id"], "prompt": prompt})

    for p in prompts:
        response = send_prompt_to_ollama(
            prompt=p["prompt"], model=args.model, host=args.host
        )
        print(f"Réponse IA pour {p['issue_id']} :\n{response}\n")


def send_prompt_to_ollama(prompt: str, model: str, host: str) -> str:
    client = Client(host=host)
    try:
        response = client.chat(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        # return response.message.content
        return response["message"]["content"]
    except Exception as e:
        logging.error(f"Erreur lors de l'appel à Ollama : {e}")
        return "Erreur lors de la génération de la réponse IA."


if __name__ == "__main__":
    main()
