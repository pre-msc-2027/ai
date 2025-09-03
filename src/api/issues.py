import logging
import os
from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse

import requests


def extract_repo_name_from_url(repo_url: str) -> Optional[str]:
    """
    Extrait le nom du repository depuis une URL Git.

    Args:
        repo_url: URL du repository (ex: "https://github.com/client_org/repo_client")

    Returns:
        Nom du repository (ex: "repo_client")
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
    api_base_url = os.getenv("API_URL", "http://localhost:8000")
    api_url = f"{api_base_url}/api/scans/analyse_with_rules/{scan_id}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        analysis = data.get("analysis", {})
        warnings = analysis.get("warnings", [])
        repo_url = analysis.get("repo_url")
        rules = data.get("rules", [])

        # Extraire le nom du workspace depuis l'URL du repo
        workspace = extract_repo_name_from_url(repo_url) if repo_url else None

        logging.info(
            f"Récupéré {len(warnings)} warnings et {len(rules)} rules depuis l'API"
        )
        if repo_url:
            logging.info(f"Repo URL: {repo_url}")
        if workspace:
            logging.info(f"Workspace détecté: {workspace}")

        return warnings, rules, workspace

    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de la récupération de l'analyse : {e}")
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
