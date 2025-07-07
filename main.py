import argparse
import logging

from ollama import Client

from src.prompt_builder import build_prompt


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

    issues = [
        {
            "id": "issue1",
            "file": "src/app.py",
            "line": 42,
            "code_snippet": "password = input('Enter password: ')",
            "rule_id": "insecure_input",
            "rule_details": {
                "description": "Ne pas utiliser input pour les mots de passe",
                "severity": "high",
            },
        }
    ]

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
        return response["message"]["content"]
    except Exception as e:
        logging.error(f"Erreur lors de l'appel à Ollama : {e}")
        return "Erreur lors de la génération de la réponse IA."


if __name__ == "__main__":
    main()
