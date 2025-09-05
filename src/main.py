import argparse
import json
import logging
import os

from dotenv import load_dotenv

from src.api.issues import get_analysis_data, post_ai_comment
from src.ollama.client import send_prompt_to_ollama
from src.prompt_builder import build_prompt
from src.utils.code_reader import extract_code_snippet


def _find_json_start(response_text):
    """Trouve le début d'un bloc JSON contenant 'original'"""
    json_start = response_text.find('{"original"')
    if json_start == -1:
        json_start = response_text.find('{ "original"')
    return json_start if json_start != -1 else None


def _find_json_end(response_text, start_pos):
    """Trouve la fin d'un bloc JSON en comptant les accolades"""
    brace_count = 0
    for i, char in enumerate(response_text[start_pos:], start_pos):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return i + 1
    return None


def _extract_json_text(response_text):
    """Extrait le texte JSON d'une réponse contenant du texte supplémentaire"""
    json_start = _find_json_start(response_text)
    if json_start is None:
        return None

    json_end = _find_json_end(response_text, json_start)
    if json_end is None:
        return None

    return response_text[json_start:json_end]


def parse_json_response(response_text):
    """
    Extrait le JSON de la réponse de l'IA, même si elle contient du texte supplémentaire
    """
    # Essayer de parser directement
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # Chercher un JSON dans le texte - Recherche sûre sans regex vulnérable
    json_text = _extract_json_text(response_text)
    if json_text:
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass

    return None


def process_warning(warning, rules_dict, workspace, args):
    """Process a single warning and return the result"""
    warning_id = warning["id"]
    rule_id = warning["rule_id"]
    file_path = warning["file"]
    line_number = warning["line"]

    logging.debug(f"Processing warning {warning_id}")
    logging.debug(f"   Rule ID: {rule_id}")
    logging.debug(f"   File: {file_path}")
    logging.debug(f"   Line: {line_number}")

    if args.verbose:
        logging.info(f"Traitement du warning {warning_id} (règle {rule_id})")

    rule = rules_dict.get(rule_id)
    if not rule:
        logging.error(f"Règle {rule_id} introuvable pour le warning {warning_id}")
        return None

    logging.debug(f"Rule found: {rule.get('name', 'Unknown')}")

    code_snippet = extract_code_snippet(file_path, line_number, workspace=workspace)
    logging.debug(f"Code snippet extracted:\n{code_snippet}")

    prompt = build_prompt(
        code_snippet=code_snippet,
        rule=rule,
        file_path=file_path,
        line_number=line_number,
    )
    logging.debug(f"Generated prompt:\n{prompt}")

    try:
        logging.debug(f"Sending prompt to Ollama (model: {args.model})")
        response = send_prompt_to_ollama(
            prompt=prompt, model=args.model, host=args.host
        )
        logging.debug(f"Raw Ollama response:\n{response}")

        logging.debug("Parsing JSON response...")
        parsed_response = parse_json_response(response)
        logging.debug(f"Parsed JSON: {parsed_response}")

        if (
            parsed_response
            and "original" in parsed_response
            and "fixed" in parsed_response
        ):
            if args.verbose:
                logging.info(f"✓ Warning {warning_id} traité avec succès")
            result = {"warning_id": warning_id, **parsed_response}
            logging.debug(f"Final result for warning {warning_id}: {result}")
            return result
        else:
            logging.error(
                f"Réponse JSON invalide pour le warning {warning_id}: "
                f"{response[:100]}..."
            )
            logging.debug(f"Full invalid response: {response}")
    except Exception as e:
        logging.error(f"Erreur lors du traitement du warning {warning_id}: {e}")
        logging.debug(f"Exception details: {type(e).__name__}: {e}")

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
        "-m",
        "--model",
        default=os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
        help="Modèle à utiliser (défaut: llama3.1:latest)",
    )
    parser.add_argument("--scan-id", required=True, help="Identifiant du scan")
    parser.add_argument(
        "-s", "--stream", action="store_true", help="Afficher la réponse en streaming"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Afficher plus de logs"
    )
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

    logging.debug(f"Starting analysis for scan ID: {args.scan_id}")
    logging.debug(f"Configuration - Model: {args.model}, Host: {args.host}")

    warnings, rules, workspace = get_analysis_data(args.scan_id)
    logging.debug(f"Retrieved data: {len(warnings)} warnings, {len(rules)} rules")
    logging.debug(f"Workspace: {workspace}")

    if not warnings:
        if args.verbose:
            logging.warning("Aucun warning trouvé dans l'analyse")
        logging.debug("Sending empty results to API")
        # Envoyer un tableau vide vers l'API
        success = post_ai_comment(args.scan_id, [])
        if not success:
            # En cas d'erreur, afficher un tableau vide localement comme fallback
            print(json.dumps([], indent=2))
        logging.debug("Empty results processing completed")
        return

    if args.verbose:
        logging.info(f"Traitement de {len(warnings)} warnings")

    logging.debug(f"Building rules dictionary from {len(rules)} rules")
    rules_dict = {rule["rule_id"]: rule for rule in rules}
    logging.debug(f"Rules available: {list(rules_dict.keys())}")

    results = []
    logging.debug(f"Starting to process {len(warnings)} warnings...")

    for i, warning in enumerate(warnings, 1):
        logging.debug(f"Processing warning {i}/{len(warnings)}")
        result = process_warning(warning, rules_dict, workspace, args)
        if result:
            results.append(result)
            logging.debug(f"Warning {i} processed successfully")
        else:
            logging.debug(f"Warning {i} failed to process")

    logging.debug(
        f"Processing completed: {len(results)}/{len(warnings)} warnings "
        f"successfully processed"
    )

    if args.verbose:
        logging.info(f"Envoi de {len(results)} résultats vers l'API...")

    logging.debug(f"Sending {len(results)} results to API endpoint")
    logging.debug(
        f"Final results to send: {json.dumps(results, indent=2, ensure_ascii=False)}"
    )

    success = post_ai_comment(args.scan_id, results)
    if success:
        if args.verbose:
            logging.info("Résultats envoyés avec succès vers l'API")
        logging.debug("API submission successful")
    else:
        logging.error("Échec de l'envoi des résultats vers l'API")
        logging.debug("API submission failed, falling back to console output")
        # En cas d'erreur, afficher les résultats localement comme fallback
        print(json.dumps(results, indent=2, ensure_ascii=False))

    logging.debug("Main processing completed")


if __name__ == "__main__":
    main()
