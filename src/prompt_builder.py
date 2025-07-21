def build_prompt(code_snippet, rule, file_path, line_number):
    return (
        f"Corrige ce problème identifié dans le fichier '{file_path}', "
        f"ligne {line_number} : {rule.get('description', 'Pas de description')}.\n\n"
        f"Code concerné :\n{code_snippet}"
    )
