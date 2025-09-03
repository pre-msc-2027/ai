import argparse
import json
import logging
import os

from dotenv import load_dotenv

from src.api.issues import get_analysis_data
from src.ollama.client import send_prompt_to_ollama
from src.prompt_builder import build_prompt
from src.utils.code_reader import extract_code_snippet


def parse_json_response(response_text):
    """
    Extrait le JSON de la réponse de l'IA, même si elle contient du texte supplémentaire
    """
    try:
        # Essayer de parser directement
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        # Chercher un JSON dans le texte
        import re

        json_pattern = r'\{[^{}]*"original"[^{}]*"fixed"[^{}]*\}'
        match = re.search(json_pattern, response_text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def process_warning(warning, rules_dict, workspace, args):
    """Process a single warning and return the result"""
    warning_id = warning["id"]
    rule_id = warning["rule_id"]
    file_path = warning["file"]
    line_number = warning["line"]

    if args.verbose:
        logging.info(f"Traitement du warning {warning_id} (règle {rule_id})")

    rule = rules_dict.get(rule_id)
    if not rule:
        logging.error(f"Règle {rule_id} introuvable pour le warning {warning_id}")
        return None

    code_snippet = extract_code_snippet(file_path, line_number, workspace=workspace)
    prompt = build_prompt(
        code_snippet=code_snippet,
        rule=rule,
        file_path=file_path,
        line_number=line_number,
    )

    try:
        response = send_prompt_to_ollama(
            prompt=prompt, model=args.model, host=args.host
        )
        parsed_response = parse_json_response(response)

        if (
            parsed_response
            and "original" in parsed_response
            and "fixed" in parsed_response
        ):
            if args.verbose:
                logging.info(f"✓ Warning {warning_id} traité avec succès")
            return {
                "warning_id": warning_id,
                "original": parsed_response["original"],
                "fixed": parsed_response["fixed"],
            }
        else:
            logging.error(
                f"Réponse JSON invalide pour le warning {warning_id}: "
                f"{response[:100]}..."
            )
    except Exception as e:
        logging.error(f"Erreur lors du traitement du warning {warning_id}: {e}")

    return None


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Outil d'analyse et correction de code avec IA"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        help="URL du serveur Ollama (défaut: localhost:11434)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
        help="Modèle à utiliser (défaut: llama3.1:latest)",
    )
    parser.add_argument("--scan-id", required=True, help="Identifiant du scan")
    parser.add_argument(
        "--stream", action="store_true", help="Afficher la réponse en streaming"
    )
    parser.add_argument("--verbose", action="store_true", help="Afficher plus de logs")
    return parser.parse_args()


def setup_logging(verbose):
    """Configure logging based on verbosity"""
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")


def log_startup_info(args):
    """Log startup information if verbose mode is enabled"""
    if args.verbose:
        logging.info(f"Lancement de l'analyse IA pour le scan {args.scan_id}")
        logging.info(f"Host Ollama: {args.host}")
        logging.info(f"Modèle: {args.model}")


def main():
    load_dotenv()
    args = parse_arguments()
    setup_logging(args.verbose)
    log_startup_info(args)

    warnings, rules, workspace = get_analysis_data(args.scan_id)

    if not warnings:
        if args.verbose:
            logging.warning("Aucun warning trouvé dans l'analyse")
        print(json.dumps([], indent=2))
        return

    if args.verbose:
        logging.info(f"Traitement de {len(warnings)} warnings")

    rules_dict = {rule["rule_id"]: rule for rule in rules}
    results = []

    for warning in warnings:
        result = process_warning(warning, rules_dict, workspace, args)
        if result:
            results.append(result)

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
