def build_prompt(code_snippet, rule, file_path, line_number):
    """
    Construit un prompt pour demander à l'IA de corriger un problème de code
    et retourner la réponse au format JSON.
    """
    rule_name = rule.get("name", "Règle inconnue")
    rule_description = rule.get(
        "Description", rule.get("description", "Pas de description")
    )
    rule_language = rule.get("language", "inconnu")
    rule_parameters = rule.get("parameters", {})

    parameters_text = ""
    if rule_parameters:
        parameters_text = f"\nParamètres de la règle : {rule_parameters}"

    return f"""Tu es un expert en correction de code {rule_language}. \
Analyse ce problème et fournis une correction.

**Problème identifié :**
- Fichier : {file_path}
- Ligne : {line_number}
- Règle : {rule_name}
- Description : {rule_description}{parameters_text}

**Code concerné :**
```{rule_language}
{code_snippet}
```

**Instructions :**
1. Identifie la ligne exacte qui pose problème
2. Propose une correction qui respecte la règle
3. Réponds UNIQUEMENT au format JSON suivant \
(sans explication supplémentaire) :

{{{"original": "ligne de code originale problématique", \
"fixed": "ligne de code corrigée"}}}

La réponse doit être un JSON valide avec les champs "original" et \
"fixed" contenant respectivement le code problématique et sa correction."""
