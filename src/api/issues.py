import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests


def extract_repo_name_from_url(repo_url: Optional[str]) -> Optional[str]:
    """
    Extrait le nom du repository depuis une URL Git.

    Args:
        repo_url: URL du repository (ex: "https://github.com/client_org/repo_client")
            ou None

    Returns:
        Nom du repository (ex: "repo_client") ou None si l'URL est invalide/vide
    """
    if not repo_url:
        return None

    try:
        # Parser l'URL
        parsed = urlparse(repo_url)

        # Extraire le chemin et supprimer les slashes
        path = parsed.path.strip("/")

        # Récupérer le dernier segment (nom du repo)
        if "/" in path:
            repo_name = path.split("/")[-1]
        else:
            repo_name = path

        # Supprimer l'extension .git si présente
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        return repo_name
    except Exception as e:
        logging.warning(f"Impossible d'extraire le nom du repo depuis {repo_url}: {e}")
        return None


def get_analysis_data(scan_id: str) -> Tuple[List[Any], List[Any], Optional[str]]:
    """
    Récupère les données d'analyse depuis l'API pour un scan donné.

    Returns:
        Tuple[warnings, rules, workspace]: Listes des warnings et rules, workspace
    """
    api_base_url = os.getenv("API_URL", "http://localhost:8001")
    api_url = f"{api_base_url}/api/scans/analyse_with_rules/{scan_id}"

    logging.debug("Making GET request to API")
    logging.debug(f"   URL: {api_url}")
    logging.debug(f"   Scan ID: {scan_id}")

    try:
        response = requests.get(api_url)
        logging.debug(f"API Response status: {response.status_code}")
        logging.debug(f"Response headers: {dict(response.headers)}")

        response.raise_for_status()
        data = response.json()
        logging.debug(f"Raw API data received: {data}")

        analysis = data.get("analysis", {})
        warnings = analysis.get("warnings", [])
        repo_url = analysis.get("repo_url")
        rules = data.get("rules", [])

        logging.debug("Parsed data:")
        logging.debug(f"   Warnings: {len(warnings)}")
        logging.debug(f"   Rules: {len(rules)}")
        logging.debug(f"   Repo URL: {repo_url}")

        # Prioriser workspace_path depuis l'API, sinon extraire depuis repo_url
        workspace_path = analysis.get("workspace_path")
        if workspace_path:
            workspace = workspace_path
            logging.debug(f"Using workspace from API: {workspace}")
        else:
            repo_name = extract_repo_name_from_url(repo_url) if repo_url else None
            workspace = f"folder/{repo_name}" if repo_name else None
            logging.debug(f"Extracted workspace from repo URL: {workspace}")

        logging.info(
            f"Récupéré {len(warnings)} warnings et {len(rules)} rules depuis l'API"
        )
        if repo_url:
            logging.info(f"Repo URL: {repo_url}")
        if workspace:
            logging.info(f"Workspace détecté: {workspace}")

        logging.debug("API data retrieval successful")
        return warnings, rules, workspace

    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de la récupération de l'analyse : {e}")
        logging.debug(f"Request exception details: {type(e).__name__}: {e}")
        return [], [], None
    except ValueError as e:
        logging.error(f"Erreur de parsing JSON : {e}")
        logging.debug(f"JSON parsing error details: {type(e).__name__}: {e}")
        return [], [], None
    except Exception as e:
        logging.error(f"Erreur lors de la récupération de l'analyse : {e}")
        logging.debug(f"Unexpected error details: {type(e).__name__}: {e}")
        return [], [], None


def get_issues(scan_id: str) -> Tuple[List[Any], Optional[str]]:
    """
    Fonction de compatibilité - utilise le nouveau format mais retourne l'ancien
    """
    warnings, rules, _ = get_analysis_data(scan_id)

    # Convertir au format attendu par l'ancien code
    issues = []
    rules_dict = {rule["rule_id"]: rule for rule in rules}

    for warning in warnings:
        rule = rules_dict.get(warning["rule_id"], {})
        issue = {
            "id": warning["id"],
            "file": warning["file"],
            "line": warning["line"],
            "rule_details": rule,
        }
        issues.append(issue)

    return issues, None


def post_ai_comment(scan_id: str, ai_results: List[Dict[str, Any]]) -> bool:
    """
    Envoie les résultats de l'analyse IA vers l'API.

    Args:
        scan_id: Identifiant du scan
        ai_results: Liste des résultats d'analyse IA

    Returns:
        bool: True si l'envoi a réussi, False sinon
    """
    api_base_url = os.getenv("API_URL", "http://localhost:8001")
    api_url = f"{api_base_url}/scans/ai_comment/{scan_id}"

    logging.debug("Preparing to POST AI results to API")
    logging.debug(f"   URL: {api_url}")
    logging.debug(f"   Scan ID: {scan_id}")
    logging.debug(f"   Results count: {len(ai_results)}")
    logging.debug(f"   Results data: {ai_results}")

    try:
        logging.debug("Making POST request...")
        response = requests.post(
            api_url,
            json=ai_results,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        logging.debug(f"POST Response status: {response.status_code}")
        logging.debug(f"Response headers: {dict(response.headers)}")

        try:
            response_data = response.json()
            logging.debug(f"Response data: {response_data}")
        except Exception:
            logging.debug(f"Response text: {response.text}")

        response.raise_for_status()

        logging.info(f"Résultats IA envoyés avec succès pour le scan {scan_id}")
        logging.debug("POST request successful")
        return True

    except requests.exceptions.RequestException as e:
        logging.error(
            f"Erreur lors de l'envoi des résultats IA pour le scan {scan_id}: {e}"
        )
        logging.debug(f"Request exception details: {type(e).__name__}: {e}")
        return False
    except Exception as e:
        logging.error(f"Erreur inattendue lors de l'envoi des résultats IA: {e}")
        logging.debug(f"Unexpected error details: {type(e).__name__}: {e}")
        return False
