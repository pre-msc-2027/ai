import logging
import os


def extract_code_snippet(
    filepath: str, line_number: int, context: int = 2, workspace: str = None
) -> str:
    """
    Extrait un snippet de code autour d'une ligne donnée.

    Args:
        filepath: Chemin vers le fichier (absolu ou relatif)
        line_number: Numéro de ligne (1-based)
        context: Nombre de lignes de contexte avant/après
        workspace: Chemin du workspace pour les fichiers relatifs

    Returns:
        Snippet de code ou message d'erreur
    """
    try:
        # Construire le chemin complet
        if workspace and not os.path.isabs(filepath):
            full_path = os.path.join(workspace, filepath)
        else:
            full_path = filepath

        logging.debug(f"Extraction du code depuis: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Handle negative line numbers by showing the whole file
        if line_number < 1:
            snippet = "".join(lines).rstrip("\n")
        else:
            start = max(line_number - context - 1, 0)
            end = min(line_number + context, len(lines))
            snippet = "".join(lines[start:end]).rstrip("\n")
        return snippet

    except FileNotFoundError:
        error_msg = (
            f"# Fichier non trouvé: "
            f"{full_path if 'full_path' in locals() else filepath}"
        )
        logging.warning(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"# Code non disponible (erreur de lecture): {e}"
        logging.warning(f"Impossible de lire le fichier {filepath} : {e}")
        return error_msg
